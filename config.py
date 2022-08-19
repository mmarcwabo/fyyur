#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import os
from urllib.parse import quote_plus
from dotenv import load_dotenv
# Load env variables
load_dotenv()
SECRET_KEY = os.urandom(32)
# Grabs the folder where the script runs.
basedir = os.path.abspath(os.path.dirname(__file__))

# Enable debug mode.
DEBUG = True

# Connect to the database
# Thanks to coach Baidou for hints, See https://github.com/badiou/session3-fsdn
db_username=quote_plus(os.getenv('DB_USERNAME'))
db_password=quote_plus(os.getenv('DB_PASSWORD'))
db_name=quote_plus(os.getenv('DB_NAME'))
SQLALCHEMY_DATABASE_URI = 'postgresql://{}:{}@localhost:5432/{}'.format(db_username, db_password, db_name)
SQLALCHEMY_TRACK_MODIFICATIONS= False