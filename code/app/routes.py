from app import application, db
from flask import render_template, redirect, url_for, \
    flash, request, session, g
from flask_login import current_user, login_user, login_required, logout_user
from app.classes import User, Data
from app.forms import LogInForm, RegistrationForm, UploadFileForm, \
    ModelResultsForm, DiseaseField, MedicationField
from app.nlp import prepare_note
from app import db, login_manager, spacy_model
from datetime import timedelta, datetime
from flask_wtf import FlaskForm
from werkzeug import secure_filename
import speech_recognition as sr
import os
import uuid
import re
import pytz


@application.route('/', methods=('GET', 'POST'))
@application.route("/index", methods=('GET', 'POST'))
def index():
    """The homepage for the website."""
    login_form = LogInForm()
    if login_form.validate_on_submit():
        username = login_form.username.data
        password = login_form.password.data
        # Look for it in the database.
        user = User.query.filter_by(username=username).first()
        # Login and validate the user.
        if user is not None and user.check_password(password):
            login_user(user)
            response = redirect(url_for('upload'))
            response.set_cookie("curr", user.id)
            return response
        else:
            flash('Invalid username and password combination!')

    return render_template('index.html', form=login_form)


@login_manager.user_loader
def load_user(id):  # id is the ID in User.
    """Finds the user with the given user id."""
    return User.query.get(id)


@application.route('/register', methods=('GET', 'POST'))
def register():
    """Page for new users to register."""
    form = RegistrationForm(request.form, null=True, blank=True)

    if form.validate_on_submit():
        ph_id = str(uuid.uuid4())
        user = User(ph_id=ph_id,
                    username=form.username.data,
                    password=form.password.data)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('register.html', form=form)


@application.route('/logout')
@login_required
def logout():
    """Log out the user."""
    logout_user()
    return redirect(url_for('index'))


@application.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    """Upload a file from a client machine."""
    file = UploadFileForm()
    if file.validate_on_submit():
        f = file.file_selector.data
        filename = secure_filename(f.filename)
        file_dir_path = os.path.join(application.instance_path, 'files')
        file_path = os.path.join(file_dir_path, filename)
        # Save file to file_path (instance/ + 'files' + filename)
        f.save(file_path)

        # Convert audio file to text (String)
        r = sr.Recognizer()
        harvard = sr.AudioFile(file_path)
        with harvard as source:
            audio = r.record(source)
        talk_to_text = r.recognize_google(audio)

        # pipe results from talk to text to nlp model
        example_result = prepare_note(spacy_model, talk_to_text)
        proper_title_keys = [k.title() for k in list(example_result.keys())]

        """Display the model results."""
        mrn = file.mrn.data
        session['example_result'] = example_result
        session['proper_title_keys'] = proper_title_keys

        session['mrn'] = mrn
        # delete the file
        if os.path.exists(file_path):
            os.remove(file_path)
        else:
            print("The file does not exist.")

        return redirect(url_for('results', filename=filename))
    return render_template('upload.html', form=file)


@application.route('/results/<filename>', methods=['GET', 'POST'])
@login_required
def results(filename):
    example_result = session.get('example_result', None)
    result = list(example_result.items())
    proper_title_keys = session.get('proper_title_keys', None)
    mrn = session.get('mrn', None)
    
    form = ModelResultsForm()

    if form.validate_on_submit():

        db_diseases = {}
        db_meds = {}
        for i in range(len(form.diseases)):
            text_field = form.diseases[i].disease.data
            split_d = [e.rstrip('\r').lower() for e in text_field.split('\n') if e != '']
            db_diseases[result[i][0]] = split_d

            text_field = form.medications[i].medication.data
            split_d = [e.rstrip('\r').lower() for e in text_field.split('\n') if e != '']
            db_meds[result[i][0]] = split_d

        current_id = request.cookies.get("curr")
        transcription_id = str(uuid.uuid4())
        row_info = list()
        tz = pytz.timezone("US/Pacific")
        timestamp = datetime.now(tz)
        for sub in proper_title_keys:
            txt = example_result[sub.lower()]["text"].lower()

            for ent_d in db_diseases[sub.lower()]:
                row_info.append((sub, txt, "disease", ent_d))

            for ent_m in db_meds[sub.lower()]:
                row_info.append((sub, txt, "medication", ent_m))

        for t in range(len(row_info)):
            sub_id = row_info[t][0]
            txt = row_info[t][1]
            entity = row_info[t][3]
            label = row_info[t][2]
            start = re.search(entity, txt).start()
            end = re.search(entity, txt).end() - 1
            upload_row = Data(id=current_id,
                              mrn=mrn,
                              transcription_id=transcription_id,
                              text=txt,
                              entity=entity,
                              start=start,
                              end=end,
                              label=label,
                              subject_id=sub_id,
                              timestamp=timestamp)
            db.session.add(upload_row)
        db.session.commit()

        return redirect(url_for('upload'))

    else:
        for i in range(len(result)):
            d_form = DiseaseField()
            m_form = MedicationField()
            disease_string = ''
            medication_string = ''

            for d in result[i][1]['diseases']:
                disease_string += d['name'].title() + u'\n'

            for m in result[i][1]['medications']:
                medication_string += m['name'].title() + u'\n'

            d_form.disease = disease_string
            m_form.medication = medication_string

            form.diseases.append_entry(d_form)
            form.medications.append_entry(m_form)

        return render_template('results.html', form=form,
                           result=result, len=len(result))
