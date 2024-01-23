from sqlalchemy import Column, Integer, String, Text, DateTime, Table, ForeignKey
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from sqlalchemy.orm import relationship


db = SQLAlchemy()

class user(db.Model, UserMixin):
    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    playlists = db.relationship("Playlist", backref="user")

    @property
    def is_active(self):

        return True


class creator(db.Model, UserMixin):
    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    full_name = Column(String(100), nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    artist_name = Column(String(100), nullable=False)
    genre = Column(String(50))
    bio = Column(Text)
    facebook = Column(String(255))
    instagram = Column(String(255))
    songs = db.relationship("Song", backref="creator", lazy="dynamic", foreign_keys='Song.creator_id')

    @property
    def is_active(self):
        
        return True


class Rating(db.Model):
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    song_id = Column(Integer, ForeignKey('song.id'), nullable=False)
    rating = Column(Integer, nullable=False)
    date = Column(DateTime, default=datetime.utcnow)

class Comment(db.Model):
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    song_id = Column(Integer, ForeignKey('song.id'), nullable=False)
    text = Column(Text, nullable=False)
    date = Column(DateTime, default=datetime.utcnow)

playlist_song_association = Table('playlist_song_association', db.Model.metadata,
    db.Column('playlist_id', db.Integer, db.ForeignKey('playlist.id')),
    db.Column('song_id', db.Integer, db.ForeignKey('song.id')) 
)

class Playlist(db.Model):
    __tablename__ = 'playlist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'))      
    songs = db.relationship("Song", secondary=playlist_song_association, backref="playlists") 

    def __repr__(self):
        return f"<Playlist {self.name}>"

class Album(db.Model):
    __tablename__ = 'album'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    date_created = Column(DateTime, default=datetime.utcnow)
    creator_name = Column(String(100), nullable=False)
    creator_id = Column(Integer, ForeignKey('creator.id'), nullable=False)
    album_songs = relationship('Song', backref='album', lazy='dynamic')
    album_icon = db.Column(db.String(100), nullable=True)
    def __repr__(self):
        return f'<Album {self.name}>'

class Song(db.Model):
    __tablename__ = 'song'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    artist = db.Column(db.String(100), nullable=False)
    album_name = db.Column(db.String(100))
    genre = db.Column(db.String(50))
    release_year = db.Column(db.Integer)
    length = db.Column(db.Integer)  
    creator_id = db.Column(db.Integer, db.ForeignKey('creator.id'))
    album_id = db.Column(db.Integer, db.ForeignKey('album.id'))
    file_path = db.Column(db.String(255), nullable=False)
    song_icon = db.Column(db.String(100), nullable=True)
    
    
    ratings = db.relationship('Rating', backref='song', lazy='dynamic')
    comments = db.relationship('Comment', backref='song', lazy='dynamic')

   

