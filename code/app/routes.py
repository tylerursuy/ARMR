from app import application, db
from flask import render_template, redirect, url_for, \
    flash, request, session, g
from flask_login import current_user, login_user, login_required, logout_user
from app.classes import User, Data, Queue
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
import json


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
            return redirect(url_for('upload', user=current_user.username))
        else:
            flash('Invalid username and password combination')

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
        username = form.username.data
        password = form.password.data
        password_confirmation = form.password_confirmation.data

        # check to see if username already exists in database
        user_count = User.query.filter_by(username=username).count()
        if user_count > 0:
            flash('Error - username ' + username + ' is taken')

        # check to see if passwords match
        elif password != password_confirmation:
            flash('Error - passwords do not match')

        else:
            user = User(username=username,
                        password=password)
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


@application.route('/upload/<user>', methods=['GET', 'POST'])
@login_required
def upload(user):
    """Upload a file from a client machine."""
    file = UploadFileForm()
    if file.validate_on_submit():
        f = file.file_selector.data
        filename = secure_filename(f.filename)

        mrn = file.mrn.data

        if filename[-4:] != '.wav':
            flash('File type must be .wav')
        elif len(str(mrn)) != 7:
            flash('MRN must be 7 digits')
        else:
            file_dir_path = os.path.join(application.instance_path, 'files')
            file_path = os.path.join(file_dir_path, filename)
            f.save(file_path)

            # Add this to the queue table
            current_id = User.query.filter_by(username=user).first().id
            transcription_id = str(uuid.uuid4())
            now_utc = pytz.utc.localize(datetime.utcnow())
            timestamp = now_utc.astimezone(pytz.timezone("America/Los_Angeles"))
            upload_row = Queue(id=current_id,
                               mrn=mrn,
                               transcription_id=transcription_id,
                               timestamp=timestamp,
                               filename=filename)
            db.session.add(upload_row)
            db.session.commit()

            return redirect(url_for('queue', user=user))
    return render_template('upload.html', form=file)


@application.route('/queue/<user>', methods=['GET', 'POST'])
@login_required
def queue(user):
    current_id = User.query.filter_by(username=user).first().id
    uploads = Queue.query.filter_by(id=current_id).order_by(Queue.timestamp.desc()).all()
    return render_template('recent_uploads.html', uploads=uploads)


@application.route('/results/<user>/<transcription>', methods=['GET', 'POST'])
@login_required
def results(user, transcription):
    queue_row = Queue.query.filter_by(transcription_id=transcription).first()
    mrn = queue_row.mrn
    example_result = json.loads(queue_row.content)
    result = list(example_result.items())
    proper_title_keys = [
                k.title() for k in list(example_result.keys())]

    form = ModelResultsForm()
    if form.validate_on_submit():

        db_diseases = {}
        db_meds = {}
        for i in range(len(form.diseases)):
            text_field = form.diseases[i].disease.data
            split_d = [
                e.rstrip('\r').lower() for e in text_field.split('\n')
                if e != '']
            db_diseases[result[i][0]] = split_d

            text_field = form.medications[i].medication.data
            split_d = [
                e.rstrip('\r').lower() for e in text_field.split('\n')
                if e != '']
            db_meds[result[i][0]] = split_d

        current_id = User.query.filter_by(username=user).first().id
        row_info = list()
        now_utc = pytz.utc.localize(datetime.utcnow())
        timestamp = now_utc.astimezone(pytz.timezone("America/Los_Angeles"))
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

            if entity in txt:
                start = re.search(entity, txt).start()
                end = re.search(entity, txt).end() - 1
            else:
                txt = entity
                start = 0
                end = len(entity) - 1

            upload_row = Data(id=current_id,
                              mrn=mrn,
                              transcription_id=transcription,
                              text=txt,
                              entity=entity,
                              start=start,
                              end=end,
                              label=label,
                              subject_id=sub_id,
                              timestamp=timestamp)
            db.session.add(upload_row)

        # Delete the row from the Queue Table
        Queue.query.filter_by(transcription_id=transcription).delete()

        db.session.commit()

        # if the query table not empty for this user, then re-direct to the queue
        # otherwise redirect to upload
        current_id = User.query.filter_by(username=user).first().id
        uploads = Queue.query.filter_by(id=current_id).first()
        if uploads:
            return redirect(url_for('queue', user=user))
        else:
            return redirect(url_for('upload', user=user))

    else:
        for i in range(len(result)):
            d_form = DiseaseField()
            m_form = MedicationField()
            disease_string = ''
            medication_string = ''

            for d in result[i][1]['diseases']:
                disease_string += d['name'].title() + '\n'

            for m in result[i][1]['medications']:
                medication_string += m['name'].title()
                if m['amount']:
                    medication_string += ' ' + m['amount']
                if m['unit']:
                    medication_string += ' ' + m['unit']
                if m['method']:
                    medication_string += ' ' + m['method']

                medication_string += '\n'

            d_form.disease = disease_string
            m_form.medication = medication_string

            form.diseases.append_entry(d_form)
            form.medications.append_entry(m_form)

        return render_template(
            'results.html', form=form, result=result, len=len(result))

    return render_template('results.html', form=form, titles=proper_title_keys,
                           result=example_result)


@application.errorhandler(401)
def unauthorized(e):
    return redirect(url_for('index'))
