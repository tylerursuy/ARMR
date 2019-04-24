from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField, \
    SelectField, FileField, IntegerField, TextAreaField
from wtforms.validators import DataRequired, InputRequired, ValidationError
from flask_wtf.file import FileRequired
from werkzeug import secure_filename


class RegistrationForm(FlaskForm):
    """A FlaskForm to register a new user."""
    username = StringField('Username (Email):', validators=[DataRequired()])
    password = PasswordField('Password:', validators=[DataRequired()])
    password_confirmation = PasswordField('Repeat Password:',
                                          validators=[DataRequired()])
    submit = SubmitField('Submit')


class LogInForm(FlaskForm):
    """A FlaskForm to log in an existing user."""
    username = StringField('Username:', validators=[DataRequired()])
    password = PasswordField('Password:', validators=[DataRequired()])
    submit = SubmitField('Login')


class UploadFileForm(FlaskForm):
    """Class for uploading file when submitted"""
    mrn = IntegerField('Medical Record Number (MRN)',
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


# # form class with static fields
# class DiseaseField(FlaskForm):
#     name = TextAreaField('Diseases')


class ModelResultsForm(FlaskForm):
    """Class for uploading file when submitted"""
    # diseases_1 = TextAreaField('Diseases')
    # diseases_2 = TextAreaField('Diseases')
    # diseases_3 = TextAreaField('Diseases')
    # diseases_4 = TextAreaField('Diseases')

    # medications_1 = TextAreaField('Medications')
    # medications_2 = TextAreaField('Medications')
    # medications_3 = TextAreaField('Medications')
    # medications_4 = TextAreaField('Medications')

    submit = SubmitField('Submit')

    def __init__(self, number_of_sections):

        self.diseases = []
        self.medications = []
        for i in range(number_of_sections):
            diseases_i = TextAreaField('Diseases')
            medication_i = TextAreaField('Medications')
            self.diseases.append(diseases_i)
            self.medications.append(medication_i)
        
        self.submit = SubmitField('Submit')
        print(self.diseases)
        print(self.diseases[0])
        print(self.diseases[0].data)
