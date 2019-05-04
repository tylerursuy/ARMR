from flask import Flask
from flask_bootstrap import Bootstrap
import os
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf import FlaskForm
import spacy
from spacy.matcher import Matcher, PhraseMatcher
from flask_apscheduler import APScheduler


# Initialization
application = Flask(__name__)
application.secret_key = os.urandom(24)
application.config.from_object(Config)
db = SQLAlchemy(application)
db.create_all()
db.session.commit()

Bootstrap(application)

# login_manager needs to be initiated before running the app
login_manager = LoginManager()
login_manager.init_app(application)

# load the spacy model
par_dir = os.path.abspath(os.path.join(os.getcwd(), os.pardir))
par_dir += "/models"
for root, dirs, files in os.walk(par_dir):
    model_dir = "{}/{}".format(par_dir, dirs[0])
    break
spacy_model = spacy.load(model_dir)

# start scheduler
scheduler = APScheduler()
scheduler.init_app(application)
scheduler.start()

from app import classes
from app import routes  # Added at the bottom to avoid circular dependencies
