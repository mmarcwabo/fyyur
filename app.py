#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import datetime
import json
import sys
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

migrate = Migrate(app, db)

# TODO: connect to a local postgresql database

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


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale='en')


app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#


@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    # num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
    venues = Location.query.all()
    for venue_location in venues:
        venue_location.venues_list = Venue.query.filter_by(
            location_id=venue_location.id).order_by('id').all()

    now = datetime.now()
    upcoming_shows_count = 0
    upcoming_shows_count = Show.query.filter(Show.show_date < now).count()

    return render_template('pages/venues.html', areas=venues, num_upcoming_shows=upcoming_shows_count)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
    # See https://docs.sqlalchemy.org/en/14/orm/query.html
    # Thanks to https://stackoverflow.com/questions/3325467/
    search_term = request.form.get('search_term', '')
    search = "%{}%".format(search_term)
    venues = Venue.query.filter(Venue.name.like(search))
    count = len(venues.all())

    response = {
        "count": count,
        "data": venues
    }
    return render_template('pages/search_venues.html', results=response)


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    # TODO: replace with real venue data from the venues table, using venue_id
    venue = Venue.query.get(venue_id)
    # upcoming_shows
    # upcoming_shows_count
    # past_shows_count

    return render_template('pages/show_venue.html', venue=venue)

#  Create Venue
#  ----------------------------------------------------------------


@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    # TODO: insert form data as a new Venue record in the db, instead
    form = VenueForm(request.form)
    venue_location = Location(city=form.city.data, state=form.state.data)
    db.session.add(venue_location)
    db.session.commit()

    # get this inserted id from database
    venue = Venue(
        name=form.name.data, location_id=venue_location.id,
        address=form.address.data, phone=form.phone.data, image_link=form.image_link.data,
        venue_genres=form.genres.data, facebook_link=form.facebook_link.data,
        venue_website=form.website_link.data, seeking_talents=form.seeking_talent.data,
        seeking_description=form.seeking_description.data
    )
    db.session.add(venue)
    db.session.commit()

    # TODO: modify data to be the data object returned from db insertion

    # on successful db insert, flash success
    flash('Venue ' + form.name.data + ' was successfully listed!')
    # TODO: on unsuccessful db insert, flash an error instead.
    # flash(u'An error occurred. Venue ' + form.name.data + ' could not be listed.', 'error')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    # TODO: Complete this endpoint for taking a venue_id, and using
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
    error = False
    try:
        venue = Venue.query.get(venue_id)
        db.session.delete(venue)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
    return redirect(url_for('index'))

    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage
    # return None

#  Artists
#  ----------------------------------------------------------------


@app.route('/artists')
def artists():
    # TODO: replace with real data returned from querying the database
    data = Artist.query.order_by('id').all()
    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".
    # See https://docs.sqlalchemy.org/en/14/orm/query.html
    # Thanks to https://stackoverflow.com/questions/3325467/
    search_term = request.form.get('search_term', '')
    search = "%{}%".format(search_term)
    artists = Artist.query.filter(Artist.name.like(search))
    count = len(artists.all())

    response = {
        "count": count,
        "data": artists
    }
    return render_template('pages/search_artists.html', results=response)


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the artist page with the given artist_id
    # TODO: replace with real artist data from the artist table, using artist_id
    artist = Artist.query.get(artist_id)
    data = artist
    return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------


@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    artist = Artist.query.get(artist_id)
    location = Location.query.get(artist.location_id)
    artist = {
        "id": artist.id,
        "name": artist.name,
        "genres": [artist.artist_genres],
        "city": location.city,
        "state": location.state,
        "phone": artist.phone,
        "website": artist.artist_website,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.seeking_venues,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link
    }
    # TODO: populate form with fields from artist with ID <artist_id>
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # TODO: take values from the form submitted, and update existing
    # artist record with ID <artist_id> using the new attributes
    artist = Artist.query.get(artist_id)
    form = ArtistForm(request.form)

    artist.name = form.name.data
    artist.phone = form.phone.data
    artist.image_link = form.image_link.data
    artist.genres = form.genres.data
    artist.facebook_link = form.facebook_link.data
    artist.artist_website=form.website_link.data
    artist.seeking_venues=form.seeking_venue.data
    artist.seeking_description=form.seeking_description.data
    # Update artist location
    artist_location = Location.query(Location).filter(Location.state == form.state.data and Location.city == form.city.data)
    if artist_location:
      artist.location_id = artist_location.id
    
    db.session.commit()

    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    venue = Artist.query.get(venue_id)
    location = Location.query.get(venue.location_id)
    venue = {
        "id": venue.id,
        "name": venue.name,
        "genres": [venue.venue_genres],
        "address": venue.address,
        "city": location.city,
        "state": location.state,
        "phone": venue.phone,
        "website": venue.venue_website,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talent,
        "seeking_description": venue.seeking_description,
        "image_link": venue.image_link
    }
    # TODO: populate form with values from venue with ID <venue_id>
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # TODO: take values from the form submitted, and update existing
    # venue record with ID <venue_id> using the new attributes
    venue = Venue.query.get(venue_id)
    form = VenueForm(request.form)

    venue.name=form.name.data
    venue.location_id=venue_location.id
    venue.address=form.address.data
    venue.phone=form.phone.data
    venue.image_link=form.image_link.data
    venue.venue_genres=form.genres.data
    venue.facebook_link=form.facebook_link.data
    venue.venue_website=form.website_link.data
    venue.seeking_talents=form.seeking_talent.data
    venue.seeking_description=form.seeking_description.data

    # Update artist location
    venue_location = Location.query(Location).filter(Location.state == form.state.data and Location.city == form.city.data)
    if venue_location:
      venue.location_id = venue_location.id
    
    db.session.commit()

    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    # called upon submitting the new artist listing form
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion
    form = ArtistForm(request.form)
    artist_location = Location(city=form.city.data, state=form.state.data)
    db.session.add(artist_location)
    db.session.commit()

    # get this inserted id from database add the venue
    artist = Artist(
        name=form.name.data, phone=form.phone.data, image_link=form.image_link.data,
        artist_genres=form.genres.data, facebook_link=form.facebook_link.data,
        artist_website=form.website_link.data, seeking_venues=form.seeking_venue.data,
        seeking_description=form.seeking_description.data, location_id=artist_location.id
    )
    db.session.add(artist)
    db.session.commit()

    # on successful db insert, flash success
    flash('Artist ' + form.name.data + ' was successfully listed!')
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    # displays list of shows at /shows
    # TODO: replace with real venues data.
    data = [{
        "venue_id": 1,
        "venue_name": "The Musical Hop",
        "artist_id": 4,
        "artist_name": "Guns N Petals",
        "artist_image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80",
        "start_time": "2019-05-21T21:30:00.000Z"
    }, {
        "venue_id": 3,
        "venue_name": "Park Square Live Music & Coffee",
        "artist_id": 5,
        "artist_name": "Matt Quevedo",
        "artist_image_link": "https://images.unsplash.com/photo-1495223153807-b916f75de8c5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=334&q=80",
        "start_time": "2019-06-15T23:00:00.000Z"
    }, {
        "venue_id": 3,
        "venue_name": "Park Square Live Music & Coffee",
        "artist_id": 6,
        "artist_name": "The Wild Sax Band",
        "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
        "start_time": "2035-04-01T20:00:00.000Z"
    }, {
        "venue_id": 3,
        "venue_name": "Park Square Live Music & Coffee",
        "artist_id": 6,
        "artist_name": "The Wild Sax Band",
        "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
        "start_time": "2035-04-08T20:00:00.000Z"
    }, {
        "venue_id": 3,
        "venue_name": "Park Square Live Music & Coffee",
        "artist_id": 6,
        "artist_name": "The Wild Sax Band",
        "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
        "start_time": "2035-04-15T20:00:00.000Z"
    }]
    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    # TODO: insert form data as a new Show record in the db, instead
    form = ShowForm(request.form)
    show = Show(artist_id=form.artist_id.data,
                venue_id=form.venue_id.data, show_date=form.start_time.data)
    db.session.add(show)
    db.session.commit()
    # on successful db insert, flash success
    flash('Show was successfully listed!')
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Show could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
