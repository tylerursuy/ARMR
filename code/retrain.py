import paramiko
from user_definition import *
from deploy import ssh_client, ssh_connection, deploy_model
from app.classes import Data
import spacy
import os
from app.nlp import train, load_model
from datetime import datetime, timedelta
import pytz
import shutil

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
    - Do not need to establish ssh connection if file is already present on server?
        - Figure out how to run bash commands from script to close screen without ssh connection


"""


def shut_down_app(ssh):
    """
    Shut down app currently running.

    :param ssh: SSH connection object
    :return: None
    """
    screen_command = "screen -S test -X quit"
    ssh.exec_command(screen_command)


def get_dir():
    """
    Load current weights.

    :return: Current model weights
             Directory to save new weights later
    """
    par_dir = os.path.abspath(os.path.join(os.getcwd(), os.pardir))
    model_dir = "{}/models/en_ner_bc5cdr_md-0.1.0".format(par_dir)
    # model_weights = load_model(model_dir)
    return model_dir


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
        if text not in text_dict.keys():
            text_dict[text] = []
        else:
            text_dict[text].append((start, end, label))

    formatted = list()
    for key, value in text_dict.items():
        formatted.append((key, {"entities": list(set(value))}))

    return formatted


def retrain(model_dir, training_data, n_iter=100):
    """
    Retrain model on last week's data.

    :param model_weights: Current model weights.
    :param training_data: Training data from past week.
    :param output_dir: Filepath to save weights.
    :param n_iter: Number of iterations to train.
    :return: None
    """
    new = train(model=model_dir,
                train_data=training_data,
                output_dir=model_dir,
                n_iter=n_iter)
    return new


def delete_old_save_new(model_dir, weights):
    shutil.rmtree(model_dir)
    weights.to_disk(model_dir)


def push_weights(weights):
    """
    Why don't we take the new weights,
    and push them somewhere else?

    :param weights: New model weights.
    :return: None
    """


def main():
    # ssh = ssh_client()
    # ssh_connection(ssh, ec2_address, user, key_file)
    raw_data = get_data()
    training_data = format_data(raw_data)
    model_dir = get_dir()
    retrain(model_dir, training_data, 5)
    # print(model_dir)
    # current_version = model_dir[97:].split(".")[1]
    # full_path = model_dir[:97]
    # new_version = "0." + str(int(current_version) + 1) + ".0"
    # full_path += new_version
    # print(full_path)
    # delete_old_save_new(model_dir, new_weights)
    # push weights
    # kill application
    # re-launch application (bash script)


if __name__ == "__main__":
    main()

