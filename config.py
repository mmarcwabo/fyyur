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
# Thanks to coach Baiou for quote_plus hint, See https://github.com/badiou/session3-fsdn
db_password=quote_plus(os.getenv('DB_PASSWORD'))
SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:{}@localhost:5432/fyyur_db'.format(db_password)
SQLALCHEMY_TRACK_MODIFICATIONS= False

