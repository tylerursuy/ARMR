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
    id = db.Column(db.String(80), primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)

    def __init__(self, ph_id, username, password):
        self.id = ph_id
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
    id = db.Column(db.String(80), nullable=False)
    mrn = db.Column(db.Integer, nullable=False)
    # id for specific transcription
    transcription_id = db.Column(db.String(80), nullable=False)
    text = db.Column(db.Text, nullable=False)
    entity = db.Column(db.Text, nullable=True)
    start = db.Column(db.Integer, nullable=True)
    end = db.Column(db.Integer, nullable=True)
    label = db.Column(db.String(100), nullable=True)
    # reason for visit, diagnosis, etc
    subject_id = db.Column(db.String(200), nullable=False)
    tz = pytz.timezone("US/Pacific")
    timestamp = db.Column(db.DateTime, default=datetime.now(tz))

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


class Queue(db.Model):
    """Schema for 'queue' table in database.
    Functions to add observations."""
    __tablename__ = "queue"
    index = db.Column(db.Integer, primary_key=True)
    id = db.Column(db.String(80), nullable=False)
    mrn = db.Column(db.Integer, nullable=False)
    # id for specific transcription
    transcription_id = db.Column(db.String(80), nullable=False)
    now_utc = pytz.utc.localize(datetime.utcnow())
    timestamp_now = now_utc.astimezone(pytz.timezone("America/Los_Angeles"))
    timestamp = db.Column(db.DateTime, default=timestamp_now)
    filename = db.Column(db.String(80), nullable=False)
    content = db.Column(db.Text, nullable=True)

    def __init__(self, id, mrn, transcription_id, timestamp, filename):
        self.id = id
        self.mrn = mrn
        self.transcription_id = transcription_id
        self.timestamp = timestamp
        self.filename = filename


@login_manager.user_loader
def load_user(id):
    """Get the user with a given user id."""
    return User.query.get(id)


db.create_all()
db.session.commit()
