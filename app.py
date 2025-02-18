#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import datetime
import sys
import dateutil.parser
import babel
from flask import render_template, request, flash, redirect, url_for
from flask_moment import Moment
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from models import app, db, Artist, Venue, Show, Location
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
import re

# for csrf usage, special thanks to coach Yacine, see https://github.com/yactouat/flask_wtf_demo
# and https://flask-wtf.readthedocs.io/en/latest/api/#module-flask_wtf.csrf
csrf = CSRFProtect(app)
csrf.init_app(app)

migrate = Migrate(app, db)
moment = Moment(app)

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


def format_genres(value):
    # display genres properly
    # first remove the { and } that surround venue genre
    value_ = value.replace('{', '')
    value_ = value_.replace('}', '')
    # then return an array of genres
    if re.search(',', value_):
        return value_.split(',')
    else:
        return [value_]


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
    # Show venues per location as locations has a venue list
    form = VenueForm()
    venues = Location.query.all()
    for venue_location in venues:
        venue_location.venues_list = Venue.query.filter_by(
            location_id=venue_location.id).order_by('id').all()

    return render_template('pages/venues.html', areas=venues, form=form)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    # search on artists with partial string search. Ensure it is case-insensitive.
    # seach for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
    # See https://docs.sqlalchemy.org/en/14/orm/query.html
    # Thanks to https://stackoverflow.com/questions/3325467/
    form = VenueForm()
    search_term = request.form.get('search_term', '')
    search = "%{}%".format(search_term)
    venues = Venue.query.filter(Venue.name.ilike(search)).all()
    count = len(venues)

    response = {
        "count": count,
        "data": venues
    }
    return render_template('pages/search_venues.html', results=response, form=form, search_term=search_term)


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    # real venue data from the venues table, using venue_id
    form = VenueForm()
    venue = Venue.query.get(venue_id)
    venue.city = Location.query.get(venue.location_id).city
    venue.state = Location.query.get(venue.location_id).state

    now = datetime.now()

    venue.genres_ = format_genres(venue.venue_genres)

    past_shows_query = db.session.query(Show).join(Venue).filter(Show.venue_id == venue_id).\
        filter(Show.show_date < now).all()
    past_shows = []
    for show in past_shows_query:
        show.artist_name = Artist.query.get(show.artist_id).name
        show.artist_image_link = Artist.query.get(show.artist_id).image_link
        show.start_time = show.show_date.isoformat()
        past_shows.append(show)
    venue.past_shows = past_shows
    venue.past_shows_count = len(past_shows)

    upcoming_shows_query = db.session.query(Show).join(Venue).filter(Show.venue_id == venue_id).\
        filter(Show. show_date > now).all()
    upcoming_shows = []
    for show in upcoming_shows_query:
        show.artist_name = Artist.query.get(show.artist_id).name
        show.artist_image_link = Artist.query.get(show.artist_id).image_link
        show.start_time = show.show_date.isoformat()
        upcoming_shows.append(show)
    venue.upcoming_shows = upcoming_shows
    venue.upcoming_shows_count = len(upcoming_shows)

    return render_template('pages/show_venue.html', venue=venue, form=form)

#  Create Venue
#  ----------------------------------------------------------------


@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    # insert form data as a new Venue record in the db
    form = VenueForm(request.form)

    if form.validate_on_submit():
        try:
            venue_location = Location(
                city=form.city.data, state=form.state.data)

            # if a location already exists, use it instead
            existing_venue_location = Location.query.filter(Location.city == form.city.data).\
                filter(Location.state == form.state.data).first()

            if (existing_venue_location):
                venue_location_id = existing_venue_location.id
            else:
                # else add the new location in the database, then use it for the venue
                db.session.add(venue_location)
                db.session.commit()
                venue_location_id = venue_location.id

            # insert the new venue to database
            venue = Venue(
                name=form.name.data, location_id=venue_location_id, address=form.address.data,
                phone=form.phone.data, image_link=form.image_link.data, venue_genres=form.genres.data,
                facebook_link=form.facebook_link.data, venue_website=form.website_link.data,
                seeking_talents=form.seeking_talent.data, seeking_description=form.seeking_description.data
            )
            db.session.add(venue)
            db.session.commit()

            # on successful db insert, flash success
            flash('Venue ' + form.name.data + ' was successfully listed!')
            return render_template('pages/home.html')
        except:
            db.session.rollback()
            db.session.close()
            flash('An error occured. ' + form.name.data + ' was not listed!')
            return render_template('forms/new_venue.html', form=form)
    else:
        flash('One or more errors found!')
        flash(form.errors)

        return render_template('forms/new_venue.html', form=form)


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
@app.route('/venues/<venue_id>/delete', methods=['GET'])
def delete_venue_on_click(venue_id):
    delete_venue(venue_id)
    flash('Venue was successfully deleted!')
    return redirect(url_for('index'))

#  Artists
#  ----------------------------------------------------------------


@app.route('/artists')
def artists():
    # TODO: replace with real data returned from querying the database
    form = ArtistForm()
    data = Artist.query.all()
    return render_template('pages/artists.html', artists=data, form=form)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".
    # See https://docs.sqlalchemy.org/en/14/orm/query.html
    # Thanks to https://stackoverflow.com/questions/3325467/
    form = ArtistForm()
    search_term = request.form.get('search_term', '')
    search = "%{}%".format(search_term)
    artists = Artist.query.filter(Artist.name.ilike(search)).all()
    count = len(artists)

    response = {
        "count": count,
        "data": artists
    }
    return render_template('pages/search_artists.html', results=response, form=form, search_term=search_term)


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the artist page with the given artist_id
    # retrieve artist data from the artist table, using artist_id
    form = ArtistForm()
    artist = Artist.query.get(artist_id)
    artist.city = Location.query.get(artist.location_id).city
    artist.state = Location.query.get(artist.location_id).state

    now = datetime.now()

    artist.genres_ = format_genres(artist.artist_genres)

    past_shows_query = db.session.query(Show).join(Artist).filter(Show.artist_id == artist_id).\
        filter(Show.show_date < now).all()
    past_shows = []
    for show in past_shows_query:
        show.venue_name = Venue.query.get(show.venue_id).name
        show.venue_image_link = Venue.query.get(show.venue_id).image_link
        # datetime format accepts only strings and char stream, not datetime
        # so converting database datetime to string
        show.start_time = show.show_date.isoformat()
        past_shows.append(show)
    artist.past_shows = past_shows
    artist.past_shows_count = len(past_shows)

    upcoming_shows_query = db.session.query(Show).join(Artist).filter(Show.artist_id == artist_id).\
        filter(Show. show_date > now).all()
    upcoming_shows = []
    for show in upcoming_shows_query:
        show.venue_name = Venue.query.get(show.venue_id).name
        show.venue_image_link = Venue.query.get(show.venue_id).image_link
        show.start_time = show.show_date.isoformat()
        upcoming_shows.append(show)
    artist.upcoming_shows = upcoming_shows
    artist.upcoming_shows_count = len(upcoming_shows)

    return render_template('pages/show_artist.html', artist=artist, form=form)

#  Update
#  ----------------------------------------------------------------


@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    artist = Artist.query.get(artist_id)
    location = Location.query.get(artist.location_id)
    artist = {
        "id": artist_id,
        "name": artist.name,
        "genres": artist.artist_genres,
        "city": location.city,
        "state": location.state,
        "phone": artist.phone,
        "website_link": artist.artist_website,
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

    form = ArtistForm(request.form)

    if form.validate_on_submit():
        try:
            artist = Artist.query.get(artist_id)
            # Update artist location
            # # If the new location exists, use it instead
            artist_location = Location.query.filter(Location.state == form.state.data).\
                filter(Location.city == form.city.data).first()
            if artist_location:
                artist.location_id = artist_location.id
            else:
                # else, add it first to locations, then use it
                artist_location = Location(
                    city=form.city.data, state=form.state.data)
                db.session.add(artist_location)
                db.session.commit()
                artist.location_id = artist_location.id

            artist.name = form.name.data
            artist.phone = form.phone.data
            artist.image_link = form.image_link.data
            artist.genres = form.genres.data
            artist.facebook_link = form.facebook_link.data
            artist.artist_website = form.website_link.data
            artist.seeking_venues = form.seeking_venue.data
            artist.seeking_description = form.seeking_description.data
            db.session.commit()
            # on successful db update, flash success
            flash('Artist ' + form.name.data + ' was successfully updated!')
            # for artist display purpose
            artist.city = Location.query.get(artist.location_id).city
            artist.state = Location.query.get(artist.location_id).state
            return render_template('pages/show_artist.html', artist=artist)
        except:
            db.session.rollback()
            db.session.close()
            flash('An error occured. Artist ' +
                  form.name.data + ' was not updated!')
            return render_template('forms/new_artist.html', form=form)
    else:
        return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    venue = Venue.query.get(venue_id)
    location = Location.query.get(venue.location_id)
    venue = {
        "id": venue.id,
        "name": venue.name,
        "genres": venue.venue_genres,
        "address": venue.address,
        "city": location.city,
        "state": location.state,
        "phone": venue.phone,
        "website": venue.venue_website,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talents,
        "seeking_description": venue.seeking_description,
        "image_link": venue.image_link
    }
    # TODO: populate form with values from venue with ID <venue_id>
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # TODO: take values from the form submitted, and update existing
    # venue record with ID <venue_id> using the new attributes

    form = VenueForm(request.form)

    if form.validate_on_submit():
        try:
            venue = Venue.query.get(venue_id)
            # Update venue location
            # # If the new location exists, use it instead
            venue_location = Location.query.filter(Location.state == form.state.data).\
                filter(Location.city == form.city.data).first()
            if venue_location:
                venue.location_id = venue_location.id
            else:
                # else, add it first to locations, then use it
                venue_location = Location(
                    city=form.city.data, state=form.state.data)
                db.session.add(venue_location)
                db.session.commit()
                venue.location_id = venue_location.id

            venue.name = form.name.data
            venue.address = form.address.data
            venue.phone = form.phone.data
            venue.image_link = form.image_link.data
            venue.venue_genres = form.genres.data
            venue.facebook_link = form.facebook_link.data
            venue.venue_website = form.website_link.data
            venue.seeking_talents = form.seeking_talent.data
            venue.seeking_description = form.seeking_description.data

            db.session.commit()
            # on successful db update, flash success

            # For venue display purpose on show_venue page
            venue.genres_=format_genres(venue.genres)
            venue.city = Location.query.get(venue.location_id).city
            venue.state = Location.query.get(venue.location_id).state

            flash('Venue ' + form.name.data + ' was successfully updated!')
            return render_template('pages/show_venue.html', venue=venue)
        except:
            db.session.rollback()
            db.session.close()
            flash('An error occured. Venue ' +
                  form.name.data + ' was not updated!')
            return render_template('forms/new_venue.html', form=form)

    else:
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

    if form.validate_on_submit:

        try:
            artist_location = Location(state = form.state.data, city = form.state.data)
            # If the new location exists, use it instead
            existing_artist_location = Location.query.filter(Location.state == form.state.data).\
                filter(Location.city == form.city.data).first()
            
            if existing_artist_location:
                artist_location_id = existing_artist_location.id
            else:
                # else, add it first to locations, then use it
                artist_location = Location(
                    city=form.city.data, state=form.state.data)
                db.session.add(artist_location)
                db.session.commit()
                artist_location_id = artist_location.id

            # get this inserted id from database add the venue
            artist = Artist(
                name=form.name.data, phone=form.phone.data, image_link=form.image_link.data,
                artist_genres=form.genres.data, facebook_link=form.facebook_link.data,
                artist_website=form.website_link.data, seeking_venues=form.seeking_venue.data,
                seeking_description=form.seeking_description.data, location_id=artist_location_id
            )
            db.session.add(artist)
            db.session.commit()

            # on successful db insert, flash success
            flash('Artist ' + form.name.data + ' was successfully listed!')
            return render_template('pages/home.html')

        except:
            db.session.rollback()
            db.session.close()
            flash(form.errors)
            flash('Artist was not listed. An error occured!')
            return render_template('forms/new_artist.html', form=form)

    else:
        flash('One or more errors found!')
        flash(form.errors)
        return render_template('forms/new_artist.html', form=form)


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    # displays list of shows at /shows
    # TODO: replace with real venues data.
    form = ShowForm()
    shows = Show.query.all()

    for show in shows:
        show.venue_name = Venue.query.get(show.venue_id).name
        show.artist_name = Artist.query.get(show.artist_id).name
        show.artist_image_link = Artist.query.get(show.artist_id).image_link
        show.start_time = show.show_date.isoformat()

    return render_template('pages/shows.html', shows=shows, form=form)


@app.route('/shows/search', methods=['POST'])
def search_shows():
    # search on artists with partial string search. Ensure it is case-insensitive.
    # seach for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
    # See https://docs.sqlalchemy.org/en/14/orm/query.html
    # Thanks to https://stackoverflow.com/questions/3325467/
    form = ShowForm()
    search_term = request.form.get('search_term', '')
    search = "%{}%".format(search_term)
    artist_shows = db.session.query(Show).join(Artist).filter(Show.artist_id == Artist.id).\
        filter(Artist.name.ilike(search)).all()
    venue_shows = db.session.query(Show).join(Venue).filter(Show.artist_id == Venue.id).\
        filter(Venue.name.ilike(search)).all()

    shows = []

    for show in artist_shows:
        show.artist_name = Artist.query.get(show.artist_id).name
        show.venue_name = Venue.query.get(show.venue_id).name
        show.start_time = show.show_date.isoformat()
        shows.append(show)
    for show in venue_shows:
        show.artist_name = Artist.query.get(show.artist_id).name
        show.venue_name = Venue.query.get(show.venue_id).name
        show.start_time = show.show_date.isoformat()
        shows.append(show)

    count = len(shows)

    response = {
        "count": count,
        "data": shows
    }
    return render_template('pages/search_shows.html', results=response, form=form, search_term=search_term)


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
    if form.validate_on_submit():
        try:
            show = Show(artist_id=form.artist_id.data,
                venue_id=form.venue_id.data, show_date=form.start_time.data)
            db.session.add(show)
            db.session.commit()
            # on successful db insert, flash success
            flash('Show was successfully listed!')
            return render_template('pages/home.html')
        except:
            db.session.rollback()
            db.session.close()
            flash(form.errors)
            flash('An error occured. Show cannot be listed')
            return render_template('forms/new_show.html', form=form)
    else:    
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
