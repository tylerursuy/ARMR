from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField, \
    SelectField, FileField, IntegerField
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
    mrn = IntegerField('MRN (Medical Record Number)',
                       validators=[InputRequired()])
    file_selector = FileField('File', validators=[FileRequired()])
    submit = SubmitField('Submit')

    def validate_mrn(form, field):
        if len(str(field.data)) != 7:
            raise ValidationError('MRN must be 7 digits.')

    def validate_file_selector(form, field):
        f = field.data
        filename = secure_filename(f.filename)
        if filename[-4:] != '.wav':
            raise ValidationError('File type must be .wav')


class ModelResultsForm(FlaskForm):
    """Class for uploading file when submitted"""
    submit = SubmitField('Submit')
