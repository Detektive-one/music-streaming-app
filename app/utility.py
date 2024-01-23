from lyricsgenius import Genius
from . import db
from .models import Rating, Comment, user, Playlist, Song, creator, Album
from datetime import datetime
import requests
from flask_login import current_user
from sqlalchemy import or_
from sqlalchemy.orm import joinedload
from werkzeug.utils import secure_filename
import os, pytz
from flask import current_app
from werkzeug.security import check_password_hash, generate_password_hash
from app import app


india_timezone = pytz.timezone('Asia/Kolkata')

token = "aN6NoJL9ThpdazOwD4PSq_eUPz_CbB7a5jRzC0x0Iwjoe7BvysKWzNsgGx9sDdpe"
genius = Genius(token, skip_non_songs=True, excluded_terms=["(Remix)", "(Live)"], remove_section_headers=True)
def get_lyrics(artist_name, song_title):    
    try:
        song = genius.search_song(song_title, artist_name)
        return song.lyrics
    except requests.exceptions.HTTPError as e:
        
        return f"Error: {e}"

def add_rating(user_id, song_id, rating):
   
    existing_rating = Rating.query.filter_by(user_id=user_id, song_id=song_id).first()

    if existing_rating:
        
        existing_rating.rating = rating
    else:
        
        new_rating = Rating(user_id=user_id, song_id=song_id, rating=rating, date=datetime.now(india_timezone))
        db.session.add(new_rating)

    db.session.commit()

def add_comment(user_id, song_id, text):
    
    new_comment = Comment(user_id=user_id, song_id=song_id, text=text,date=datetime.now(india_timezone) )
    db.session.add(new_comment)
    db.session.commit()

def get_song_comments(song_id):
    comments = Comment.query.filter_by(song_id=song_id).all()
    comment_data = []

    for comment in comments:
        user_id = user.query.get(comment.user_id)
        comment_info = {
            'song_name': Song.query.filter_by(id=song_id).first().title,
            'id': comment.user_id,
            'username': user_id.username,
            'timestamp': datetime.strftime(comment.date, "%Y-%m-%d %H:%M:%S"),
            'text': comment.text
        }
        comment_data.append(comment_info)

    return comment_data

def calculate_average_rating(song_id):
    
    ratings = Rating.query.filter_by(song_id=song_id).all()

    if not ratings:
        return None

    total_rating = sum([rating.rating for rating in ratings])
    average_rating = total_rating / len(ratings)

    return average_rating

def create_playlist(playlist_name, creator_id):
    new_playlist = Playlist(name=playlist_name, creator_id=creator_id)
    db.session.add(new_playlist)
    db.session.commit()

def add_songs_to_playlist(playlist_id, song_id):
    try:
        playlist = Playlist.query.get(playlist_id)
        if not playlist:
            raise Exception("no fount.")

        song = Song.query.get(song_id)
        if not song:
            raise Exception("errror not founf.")             
        playlist.songs.extend([song])
        app.logger.info(f'User {current_user.username} added {song.title} to his playlist {playlist.name}')   

        db.session.commit()
        print("song aded.", "success")
    except Exception as e:
        db.session.rollback()
        print(f"Error: {str(e)}", "not working")

def get_user_playlists(creator_id):
    return Playlist.query.filter_by(creator_id=creator_id).all()

def search_song(query):

    songs = Song.query.filter(
            or_(
                Song.title.ilike(f"%{query}%"),
                Song.artist.ilike(f"%{query}%"),
                Song.genre.ilike(f"%{query}%")
            )
        ).all()
    return songs

def get_songs_in_playlist(playlist_id):
    playlist = Playlist.query.filter_by(id=playlist_id).options(joinedload(Playlist.songs)).first()

    if playlist:
        songs_details = []
        for song in playlist.songs:
            song_details = {
                'title': song.title,
                'song_icon': song.song_icon,
                'file_path': song.file_path,
            }
            songs_details.append(song_details)
        return songs_details
    else:
        return None

def get_creator_info(creator_id):
    try:
        
        creator_info = creator.query.filter_by(id=creator_id).first()
        return creator_info
    except Exception as e:
        print(f"Error retrieving creator information: {e}")
        return None
    
def add_song(title, artist, album_name, genre, length, release_year, creator_id, audio_file, icon_file):
   
    new_song = Song(
        title=title,
        artist=artist,
        album_name=album_name,
        genre=genre,
        length = length,
        release_year=release_year,
        creator_id=creator_id
    )

  
    audio_filename = save_file(audio_file, allowed_extensions=['mp3'])
    audio_path = 'songs/'+audio_filename
    new_song.file_path = audio_path
    print(audio_path)

    duration = 123
    new_song.length = duration

    icon_filename = save_file(icon_file, allowed_extensions=['png', 'jpg', 'jpeg'])
    new_song.song_icon = 'icons/'+icon_filename

    db.session.add(new_song)
    db.session.commit()

    return new_song

def save_file(file, allowed_extensions):
    if file:
        filename = secure_filename(file.filename)
        if '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions:
            root = os.path.dirname(current_app.root_path)
            
            if filename.lower().endswith('.mp3'):
                destination_folder = 'songs'
            elif filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                destination_folder = 'icons'
            else:
                print('err')

            file.save(os.path.join(root, 'static', destination_folder, filename))
            return filename
    print("err")

def create_album(album_name, album_icon, creator_id, creator_name):

    album_icon_filename = save_file(album_icon, allowed_extensions=['png', 'jpg', 'jpeg'])
    icon_path = 'icons/'+album_icon_filename
    
    
    new_album = Album(
        name=album_name,
        date_created=datetime.now(india_timezone),
        creator_name=creator_name, 
        creator_id=creator_id,
        album_icon=icon_path
    )

    
    db.session.add(new_album)
    db.session.commit()

    return new_album

def update_password(creator_id, old_password, new_password, confirm_new_password):

    creator_user = creator.query.filter_by(id=creator_id).first()
    if not check_password_hash(creator_user.password, old_password):
        print(old_password)
        print(current_user.password)
        print('Incorrect old password. Please try again.', 'error')
        return

    
    if new_password != confirm_new_password:
        print('New password and confirm new password do not match. Please try again.', 'error')
        return

    
    hashed_password = generate_password_hash(new_password, method='pbkdf2:sha256')
    
    

    creator_user.password = hashed_password
    db.session.commit()

    print('Password successfully changed.', 'success')


from sqlalchemy import func

def get_stats(keyword):

    if keyword == "user":
        total_users = len(user.query.all())
        total_ratings = len(Rating.query.all())
        total_comments = len(Comment.query.all())
        total_playlists = len(Playlist.query.all())

        stats = {
            'Total Playlists': total_playlists,
            'Total Comments': total_comments,
            'Total Ratings': total_ratings,
            'Total Users': total_users
        }


        return stats
    
  
