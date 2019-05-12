import paramiko
from user_definition import *
from deploy import ssh_client, ssh_connection, deploy_model
from app.classes import Data
import spacy
import os
from app.nlp import train, load_model
from datetime import datetime, timedelta
import pytz
import tarfile
import boto3
from app import spacy_model

"""
Work Flow:

Step One: Grab current model weights.
Step Two: Pull down training data from DB from past week.
Step Three: Make sure training data is formatted correctly for SpaCy.
Step Four: Train model on new data.
Step Five: Push new model weights to S3.
Step Six: Kill app.
Step Seven: Delete old weights?
Step Seven: Re-Deploy app.

Notes:
    - Do not need to establish ssh connection if file is already present
    on server?
        - Figure out how to run bash commands from script to close screen
        without ssh connection
"""


def shut_down_app():
    """
    Shut down app currently running.

    :param ssh: SSH connection object
    :return: None
    """
    screen_command = "screen -S test -X quit"
    os.system(screen_command)


def get_dir():
    """
    Load current weights.

    :return: Current model weights
             Directory to save new weights later
    """
    par_dir = os.path.abspath(os.path.join(os.getcwd(), os.pardir))
    par_dir += "/models"
    for root, dirs, files in os.walk(par_dir):
        model_dir = "{}/{}".format(par_dir, dirs[0])
        break
    return model_dir, par_dir


def get_data():
    """
    Query training data from most recent week.

    :return: Training data
    """
    today_utc = pytz.utc.localize(datetime.utcnow())
    today_pst = today_utc.astimezone(pytz.timezone("America/Los_Angeles"))
    one_week_ago = today_pst - timedelta(days=7)
    raw_data = Data.query.filter(Data.timestamp > one_week_ago).all()
    train_data = [row.__repr__().split("/col/") for row in raw_data]
    return train_data


def format_data(training_data):
    """
    Format data into Spacy readable format.

    :param training_data: Training data
    :return: Formatted data
    """
    text_dict = dict()
    for row in training_data:
        text = row[3]
        start = int(row[5])
        end = int(row[6])
        label = row[7].upper()
        if label == "MEDICATION":
            label = "CHEMICAL"
        if start + end > 0:
            if text not in text_dict.keys():
                text_dict[text] = []
                text_dict[text].append((start, end, label))
            else:
                text_dict[text].append((start, end, label))

    formatted = list()
    for key, value in text_dict.items():
        formatted.append((key, {"entities": list(set(value))}))

    return formatted


def retrain(model, training_data, output_dir, n_iter=100):
    """
    Retrain model on last week's data.

    :param model: Current model weights.
    :param training_data: Training data from past week.
    :param n_iter: Number of iterations to train.
    :return: None
    """
    nlp, path = train(model=model,
                      train_data=training_data,
                      output_dir=output_dir,
                      n_iter=n_iter)
    return nlp, path


def to_zip(model_dir):
    os.chdir(f"../models")
    zip_file = f"{model_dir}.zip"
    os.system(f"zip -r {zip_file} {str(model_dir).split('/')[-1]}/*")
    print(f"Zipped to {model_dir}")
    return zip_file


def push_weights(zip_file):
    """
    Why don't we take the new weights,
    and push them somewhere else?

    :param tar_file: New model weights tar file.
    :return: None
    """
    s3 = boto3.client('s3')
    bucket_name = 'msds-armr'

    # Uploads the given file using a managed uploader,
    # which will split up large
    # files automatically and upload parts in parallel.
    s3.upload_file(zip_file, bucket_name, zip_file,
                   ExtraArgs={'ACL': 'public-read'})


def redeploy():
    os.system("bash flask.sh")


def main():
    raw_data = get_data()
    training_data = format_data(raw_data)
    model_dir, par_dir = get_dir()
    nlp, path = retrain(model_dir, training_data, model_dir, 5)
    zipped = to_zip(path)
    to_s3 = str(zipped).split("/")[-1]
    push_weights(to_s3)
    shut_down_app()
    redeploy()


if __name__ == "__main__":
    main()
