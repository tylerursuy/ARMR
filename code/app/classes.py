from flask_login import UserMixin
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash
from app import db, login_manager
from flask_wtf.file import FileField, FileRequired
from datetime import datetime
import pytz


class User(db.Model, UserMixin):
    """Schema for 'users' table in database.
    Functions to add observations."""
    __tablename__ = "users"
    id = db.Column(db.Integer, db.Sequence('id'), primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)

    def __init__(self, username, password):
        self.username = username
        self.set_password(password)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Verification(db.Model):
    """A class of methods to check whether a password is valid."""
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(120), nullable=False)

    def __init__(self, code):
        self.code = code

    def check_code(self, input):
        return check_password_hash(self.code, input)

    def check_pwd_digit(self, input):
        return any([x.isdigit() for x in input])

    def check_pwd_upper(self, input):
        return any([x.isupper() for x in input])

    def check_pwd_length(self, input):
        return len(input) >= 8


class Data(db.Model):
    """Schema for 'transcriptions' table in database.
    Functions to add observations."""
    __tablename__ = "transcriptions"
    index = db.Column(db.Integer, primary_key=True)
    id = db.Column(db.Integer, nullable=False)
    mrn = db.Column(db.Integer, nullable=False)
    transcription_id = db.Column(db.String(80), nullable=False)
    text = db.Column(db.Text, nullable=False)
    entity = db.Column(db.Text, nullable=True)
    start = db.Column(db.Integer, nullable=True)
    end = db.Column(db.Integer, nullable=True)
    label = db.Column(db.String(100), nullable=True)
    subject_id = db.Column(db.String(200), nullable=False)
    timestamp = db.Column(db.DateTime)

    def __init__(self, id, mrn, transcription_id, text, entity,
                 start, end, label, subject_id, timestamp):
        """Notes:
         - physician_id should be automatically set after logging in, not input
           each time
         - transcription_id should be  generated per transcription upload"""
        # self.index = index
        self.id = id
        self.mrn = mrn
        self.transcription_id = transcription_id
        # text per section (i.e. diagnosis, RFV, prescription, etc)
        self.text = text
        # text selected from model as medical entity from section text
        self.entity = entity
        self.start = start  # start index of entity in text
        self.end = end  # end index of entity in text
        self.label = label  # label given from model for entity
        # subject id that maps to EMR sections (i.e. diagnosis, RFV,
        # prescription, etc)
        self.subject_id = subject_id
        self.timestamp = timestamp

    def __repr__(self):
        info = (self.id, self.mrn, self.transcription_id, self.text,
                self.entity, self.start, self.end, self.label,
                self.subject_id, self.timestamp)
        row = ""
        m = len(info) - 1
        for r in range(len(info)):
            if r != m:
                row += str(info[r]) + "/col/"
            else:
                row += str(info[r])
        return row


class Queue(db.Model):
    """Schema for 'queue' table in database.
    Functions to add observations."""
    __tablename__ = "queue"
    index = db.Column(db.Integer, primary_key=True)
    id = db.Column(db.Integer, nullable=False)
    mrn = db.Column(db.Integer, nullable=False)
    transcription_id = db.Column(db.String(80), nullable=False)
    timestamp = db.Column(db.DateTime)
    filename = db.Column(db.String(80), nullable=False)
    content = db.Column(db.Text, nullable=True)

    def __init__(self, id, mrn, transcription_id, timestamp, filename):
        self.id = id
        self.mrn = mrn
        self.transcription_id = transcription_id
        self.timestamp = timestamp
        self.filename = filename


class History(db.Model):
    """Schema for 'queue' table in database.
    Functions to add observations."""
    __tablename__ = "history"
    index = db.Column(db.Integer, primary_key=True)
    id = db.Column(db.Integer, nullable=False)
    mrn = db.Column(db.Integer, nullable=False)
    transcription_id = db.Column(db.String(80), nullable=False)
    timestamp = db.Column(db.DateTime)
    filename = db.Column(db.String(80), nullable=False)
    content = db.Column(db.Text, nullable=False)
    diseases = db.Column(db.Text, nullable=False)
    meds = db.Column(db.Text, nullable=False)

    def __init__(self, id, mrn, transcription_id, timestamp, filename,
                 content, diseases, meds):
        self.id = id
        self.mrn = mrn
        self.transcription_id = transcription_id
        self.timestamp = timestamp
        self.filename = filename
        self.content = content
        self.diseases = diseases
        self.meds = meds


@login_manager.user_loader
def load_user(id):
    """Get the user with a given user id."""
    return User.query.get(id)


db.create_all()
db.session.commit()
