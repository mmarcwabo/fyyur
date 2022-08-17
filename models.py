from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask import Flask

app = Flask(__name__)
# import configurations

app.config.from_object('config')

db = SQLAlchemy(app)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#


class Venue(db.Model):
    __tablename__ = 'venues'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))

    # TODO: implement any missing fields, as a database migration using Flask-Migrate
    seeking_talents = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(500))
    venue_genres = db.Column(db.String(500))
    venue_website = db.Column(db.String(500))
    location_id = db.Column(db.Integer, db.ForeignKey(
        'locations.id'), nullable=True)
    shows = db.relationship('Show', backref='venue_shows', lazy=True)


class Artist(db.Model):
    __tablename__ = 'artists'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))

    # TODO: implement any missing fields, as a database migration using Flask-Migrate
    seeking_venues = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(500))
    artist_genres = db.Column(db.String(500))
    artist_website = db.Column(db.String(500))
    location_id = db.Column(db.Integer, db.ForeignKey(
        'locations.id'), nullable=True)
    shows = db.relationship('Show', backref='artist_shows', lazy=True)

# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.


class Show(db.Model):
    __tablename__ = 'shows'

    id = db.Column(db.Integer, primary_key=True)
    # show star_time in datetime
    show_date = db.Column(db.DateTime(), nullable=True)
    artist_id = db.Column(db.Integer, db.ForeignKey(
        'artists.id'), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey(
        'venues.id'), nullable=False)

# Avoid data duplication in venue and artist relations (3rd nf)


class Location(db.Model):
    __tablename__ = 'locations'

    id = db.Column(db.Integer, primary_key=True)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    artists = db.relationship('Artist', backref='artist_location', lazy=True)
    venues = db.relationship('Venue', backref='venue_location', lazy=True)
