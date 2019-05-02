from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField, \
    SelectField, FileField, IntegerField, TextAreaField, FieldList, FormField
from wtforms.validators import DataRequired, InputRequired, ValidationError
from flask_wtf.file import FileRequired
from werkzeug import secure_filename


class RegistrationForm(FlaskForm):
    """A FlaskForm to register a new user."""
    username = StringField('Email (Username):', validators=[DataRequired()])
    password = PasswordField('Password:', validators=[DataRequired()])
    password_confirmation = PasswordField('Repeat Password:',
                                          validators=[DataRequired()])
    submit = SubmitField('Submit')


class LogInForm(FlaskForm):
    """A FlaskForm to log in an existing user."""
    username = StringField('Email:', validators=[DataRequired()])
    password = PasswordField('Password:', validators=[DataRequired()])
    submit = SubmitField('Login')


class UploadFileForm(FlaskForm):
    """Class for uploading file when submitted"""
    mrn = StringField('MRN (Medical Record Number)',
                       validators=[InputRequired()])
    file_selector = FileField('File', validators=[FileRequired()])
    submit = SubmitField('Submit')


class DiseaseField(FlaskForm):
    """form class with static fields for Disease"""
    disease = TextAreaField()


class MedicationField(FlaskForm):
    """form class with static fields Medication"""
    medication = TextAreaField()


class ModelResultsForm(FlaskForm):
    """Class for uploading file when submitted"""
    history_present_diseases = FormField(DiseaseField)
    history_past_diseases = FormField(DiseaseField)
    history_social_diseases = FormField(DiseaseField)
    assessment_diseases = FormField(DiseaseField)

    medications = FormField(MedicationField)
    allergy_medications = FormField(MedicationField)

    submit = SubmitField('Submit')

