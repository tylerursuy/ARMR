class Config(object):
    """Connect to database."""
    user = "armrMaster"  # replace with server username
    pw = "armr_pw603"  # replace with server password
    SQLALCHEMY_DATABASE_URI = f"postgresql://{user}:\
{pw}@armr.c4eooxhj8ss8.us-west-1.rds.amazonaws.com:5432/armr"
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    SCHEDULER_API_ENABLED = True
