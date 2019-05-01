class Config(object):
    """Connect to database."""
    user = "armrMaster"  # replace with server username
    pw = "armr_pw603"  # replace with server password
    SQLALCHEMY_DATABASE_URI = f"postgresql://{user}:\
{pw}@armr.c4eooxhj8ss8.us-west-1.rds.amazonaws.com:5432/armr"
    SQLALCHEMY_TRACK_MODIFICATIONS = True

    # APSchedule
    JOBS = [
        {
            'id': 'job1',
            'func': 'config:job1',
            'args': (1, 2),
            'trigger': 'interval',
            'seconds': 10
        }
    ]
    SCHEDULER_API_ENABLED = True


def job1(a, b):
    print(str(a) + ' ' + str(b))
