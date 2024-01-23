from flask import render_template, request, redirect, url_for, session, jsonify, make_response
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, current_user , logout_user
from app import app
from app.models import user, db, creator, Song, Playlist, Album, Comment, Rating
from functools import wraps
from app.utility import get_lyrics, add_rating, add_comment,  get_stats ,calculate_average_rating, add_song, update_password, create_album, get_song_comments, get_creator_info, create_playlist, get_user_playlists, add_songs_to_playlist, search_song, get_songs_in_playlist
import os
from sqlalchemy import text
import logging




@app.route('/')
def index():
    
    return render_template('index.html')

@app.route('/register/user', methods=['GET', 'POST'])
def register_user():
       
    form_fields = [
        {'id': 'username', 'label': 'Username', 'name': 'username', 'type': 'text', 'required': True},
        {'id': 'email', 'label': 'Email', 'name': 'email', 'type': 'email', 'required': True},
        {'id': 'password', 'label': 'Password', 'name': 'password', 'type': 'password', 'required': True},
        {'id': 'confirm_password', 'label': 'Confirm Password', 'name': 'confirm_password', 'type': 'password', 'required': True},
         ]
    if request.method == 'POST':        
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')    
       
        if password != confirm_password:
            print('Passwords do not match. Please try again.', 'error')
            return redirect(url_for('register_user'))
        
        existing_user = user.query.filter((user.username == username) | (user.email == email)).first()
        if existing_user:
            print('Username or email is already in use. Please choose different credentials.', 'error')
            return redirect(url_for('register_user'))

        
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
       
        new_user = user(            
            username=username,
            email=email,
            password=hashed_password,            
        )
        db.session.add(new_user)
        db.session.commit()       
        app.logger.info(f'New User Registered : {username}') 

        
        
        return redirect(url_for('login'))

    return render_template('register_user.html', form_fields=form_fields)


@app.route('/register/creator', methods=['GET', 'POST'])
def register_creator():
    is_user = session.get('is_user', False)
    if request.method == 'POST':
       
        username = request.form['username']
        full_name = request.form['full_name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        artist_name = request.form['artist_name']
        genre = request.form['genre']
        bio = request.form['bio']
        facebook = request.form['facebook']
        instagram = request.form['instagram']
        
        if password != confirm_password:
            return render_template('register_creator.html', error='Passwords do not match.')
        
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')     
        new_creator = creator(
            username=username,
            full_name=full_name,
            email=email,
            password=hashed_password,  
            artist_name=artist_name,
            genre=genre,
            bio=bio,
            facebook=facebook,
            instagram=instagram           
        )       
        db.session.add(new_creator)
        db.session.commit()
        app.logger.info(f'New Creator Registered : {username} , {full_name}') 
        return redirect(url_for('login'))
    
    if is_user:
        user_email = current_user.email
        user_username = current_user.username
        return render_template('register_creator.html', user_email=user_email, user_username=user_username)
    return render_template('register_creator.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        remember = request.form.get('rememberMe') 

        regular_user = user.query.filter_by(username=username).first()
        creator_user = creator.query.filter_by(username=username).first()

        user_to_login = None
        if creator_user and check_password_hash(creator_user.password, password) and creator_user.is_active:
            user_to_login = creator_user
            session.pop('is_user', None)  
            session['is_creator'] = True            

        elif regular_user and check_password_hash(regular_user.password, password) and regular_user.is_active:
            user_to_login = regular_user
            session.pop('is_creator', None)  
            session['is_user'] = True
            
        if user_to_login:
            login_user(user_to_login, remember=remember)
            app.logger.info(f'User {username} logged in')
            
            print('Login successful!')
            return redirect(url_for('user_dashboard'))

        print('Invalid username or password. Please try again.', 'error')

    return render_template('login.html')

@app.route('/forgot_password')
def forgot_password():
    
    return render_template('index.html')

@app.route('/logout')
@login_required
def logout():
    session.pop('is_user', None)
    session.pop('is_creator', None)
    session.clear()
    logout_user()
    
    response = make_response(redirect(url_for('index')))
    response.delete_cookie('session')
    
    return response

@app.route('/user/dashboard')
@login_required
def user_dashboard():
    app.logger.info(f'{current_user.username} accessed the user dashboard')
    is_creator = session.get('is_creator', False)
    albums = Album.query.all()
    
    songs = Song.query.all()

    
    
    return render_template('user_dashboard.html', user=current_user, albums=albums, songs=songs , is_creator = is_creator, register_creator=register_creator)


@app.route('/search_results', methods=['GET'])
@login_required
def search_results():
    is_creator = session.get('is_creator', False)
    query = request.args.get('query', '')
    songs = search_song(query)

    
    if query:
        logging.info(f'Search query: {query}')

    
    if songs:
        logging.info('Search result songs:')
        for song in songs:
            logging.info(f'Song {song.title} appeared in a search for {query}')

  
    if not any(song.title.lower() == query.lower() for song in songs):
        logging.info(f'Searched for: {query}')

    return render_template('search_results.html', query=query, songs=songs, is_creator=is_creator)


@app.route('/song/<int:song_id>', methods=['GET', 'POST'])
@login_required
def song_player( song_id):
    is_creator = session.get('is_creator', False)
    song = Song.query.get(song_id)
    lyrics = "Instrumental songs have no lyrics"
    app.logger.info(f'Song {song.title} was opened')

   
    if song.genre != "Instrumental":
        lyrics = get_lyrics(song.artist, song.title)
              

    if 'rating' in request.form:
        rating = int(request.form['rating'])
        add_rating(current_user.id, song_id, rating)
        app.logger.info(f'User {current_user.username} rated a song')
        app.logger.info(f'{song.title} got a rating : {rating} ')
        return redirect(url_for('song_player', song_id=song_id))

    if 'comment' in request.form:
        comment_text = request.form['comment']
        add_comment(current_user.id, song_id, comment_text)
        app.logger.info(f'User {current_user.username} commented on a song')
        app.logger.info(f'{song.title} got a comment : {comment_text} ')
        return redirect(url_for('song_player', song_id=song_id))

    average_rating = (calculate_average_rating(song_id))
    comments = get_song_comments(song_id)
    

    return render_template('song_player.html', song=song, lyrics=lyrics, average_rating=average_rating, comments = comments, is_creator=is_creator)

@app.route('/profile' ,  methods=['GET', 'POST'])
@login_required
def profile():
    is_creator = session.get('is_creator', False)
    
    if request.method == 'POST':
        action = request.form.get('action')
        from_modal = request.form.get('from_modal') == 'true'

        if action == 'create_playlist':
            playlist_name = request.form.get('playlist_name')
            create_playlist(playlist_name, current_user.id)
            app.logger.info(f'User {current_user.username} created a playlist')
            return redirect(url_for('profile'))


        elif action == 'add_songs_to_playlist':
            playlist_id = request.form.get('playlist_id')
            song_ids = request.form.get('song_ids')
            print(song_ids)
            add_songs_to_playlist(playlist_id, song_ids)
            
            return redirect(url_for('profile'))
        
        elif action == 'change_name':
            playlist_id = request.form.get('playlist_id')
            new_playlist_name = request.form.get('new_playlist_name')
            playlist = Playlist.query.get(playlist_id)
            app.logger.info(f'User {current_user.username} changed {playlist.name} to {new_playlist_name}') 
            playlist.name = new_playlist_name
            db.session.commit()
              
            return redirect(url_for('profile'))

        elif action == 'delete_playlist':
            playlist_id = request.form.get('playlist_id')
            playlist = Playlist.query.get(playlist_id)
            db.session.delete(playlist)
            db.session.commit()
            app.logger.info(f'User {current_user.username} deleted  playlist : {playlist.name} ') 

            return redirect(url_for('profile'))

        
        elif from_modal is True:
            query = request.form.get('search_text', '')
            song_searched = search_song(query)
            
            return jsonify({'songs': [{'id': song.id, 'title': song.title, 'artist': song.artist} for song in song_searched]})

   
    songs = Song.query.all()
    playlists = get_user_playlists(current_user.id)

    return render_template('profile.html', current_user=current_user, songs=songs,  playlists=playlists, is_creator=is_creator)

@app.route('/playlist/<int:playlist_id>' ,  methods=['GET', 'POST'])
@login_required
def playlist(playlist_id):   
    playlist = Playlist.query.get(playlist_id)
    is_creator = session.get('is_creator', False)
    
    if request.method == 'POST':
        action = request.form.get('action')
        from_modal = request.form.get('from_modal') == 'true'

        if action == 'add_songs_to_playlist':
            song_ids = request.form.get('song_ids')
            print(song_ids)
            add_songs_to_playlist(playlist_id, song_ids)
            
            return redirect(url_for('playlist', playlist_id=playlist_id))
        
        elif action == 'change_name':
            
            new_playlist_name = request.form.get('new_playlist_name')
            playlist = Playlist.query.get(playlist_id)
            app.logger.info(f'User {current_user.username} changed {playlist.name} to {new_playlist_name}') 
            playlist.name = new_playlist_name
            db.session.commit()
            return redirect(url_for('playlist', playlist_id=playlist_id))

        elif action == 'delete_playlist':
            
            playlist = Playlist.query.get(playlist_id)
            db.session.delete(playlist)
            db.session.commit()
            app.logger.info(f'User {current_user.username} deleted  playlist : {playlist.name} ') 

            return redirect(url_for('playlist', playlist_id=playlist_id))

        
        elif from_modal is True:
            query = request.form.get('search_text', '')
            song_searched = search_song(query)
            print(song_searched)
            return jsonify({'songs': [{'id': song.id, 'title': song.title, 'artist': song.artist} for song in song_searched]})
    
    songs = get_songs_in_playlist(playlist_id)  
    print(songs)      

    return render_template('playlist.html', playlist=playlist , songs = songs, is_creator=is_creator)

#creator routes
@app.route('/creator/dashboard', methods=['GET', 'POST'])
@login_required
def creator_dashboard():
    is_creator = session.get('is_creator', False)

    creator_info = get_creator_info(current_user.id)

    if request.method == 'POST':
        if 'audio_file' in request.files:
            
            title = request.form.get('title')
            artist = request.form.get('artist')
            album = request.form.get('album')
            genre = request.form.get('genre')
            length = request.form.get('length')
            release_year = request.form.get('release_year')
            creator_id = request.form.get('creator_id')
            audio_file = request.files.get('audio_file')
            icon_file = request.files.get('icon_file')
            add_song(title, artist, album, genre, length, release_year, creator_id, audio_file, icon_file)
            app.logger.info(f'Creator {creator_info.full_name} added a song')
            app.logger.info(f'New song was added : {title} ')
        elif 'album_name' in request.form:
            
            album_name = request.form.get('album_name')
            album_icon = request.files.get('album_icon')
            creator_id = request.form.get('creator_id')
            creator_name = creator_info.full_name
            create_album(album_name, album_icon, creator_id, creator_name)
            app.logger.info(f'Creator {creator_info.full_name} created a new album')
            app.logger.info(f'New Album was created : {album_name}')

        elif 'new_username' in request.form:
            new_username = request.form.get('new_username')

            creator_info.username = new_username
            db.session.commit()
            app.logger.info(f'Creator {creator_info.full_name} changed their username : { new_username}')
            
        elif 'new_email' in request.form:
            new_email = request.form.get('new_email')
            creator_info.email = new_email
            db.session.commit()
            app.logger.info(f'Creator {creator_info.full_name} changed their email : { new_email}')
            

        elif 'old_password' in request.form and 'new_password' in request.form and 'confirm_new_password' in request.form:
            old_password = request.form.get('old_password')
            new_password = request.form.get('new_password')
            confirm_new_password = request.form.get('confirm_new_password')
            update_password(current_user.id, old_password, new_password, confirm_new_password)
        
        return redirect(url_for('creator_dashboard'))
   
    songs = Song.query.filter(Song.creator_id == current_user.id)
    albums = Album.query.filter(Album.creator_id == current_user.id)
   
    return render_template('creator_dashboard.html', current_user=current_user, is_creator=is_creator, creator_info=creator_info, songs=songs, albums=albums)


@app.route('/album/<int:album_id>' ,  methods=['GET', 'POST'])
@login_required
def album(album_id):
    is_creator = session.get('is_creator', False)
    album = Album.query.get(album_id)
    app.logger.info(f'Album {album.name} was opened')

    if request.method == 'POST':
        from_modal = request.form.get('from_modal') == 'true'        
        selected_song_ids = request.form.getlist('selected_songs')
        action = request.form.get('action')

        if from_modal is True:
            query = request.form.get('search_text', '')
            song_searched = search_song(query)
            
            return jsonify({'songs': [{'id': song.id, 'title': song.title, 'artist': song.artist} for song in song_searched]})
        
        if action == 'change_name':
            new_album_name = request.form.get('new_album_name')
            album = Album.query.get(album_id)
            album.name = new_album_name
            db.session.commit()
            app.logger.info(f'Album {album.name} changed to : { new_album_name}')
            
            songs = Song.query.filter(Song.album_id == album_id).all()
            for song in songs:
                song.album_name = new_album_name
            db.session.commit()
        
        if action == 'delete_album':
            album = Album.query.get(album_id)
            songs = Song.query.filter(Song.album_id == album_id).all()
            for song in songs:
                song.album_name = None
            db.session.commit()

            db.session.delete(album)
            db.session.commit()
            app.logger.info(f'Album {album.name} changed was deleted')
            return redirect(url_for('creator_dashboard'))

        
        for song_id in selected_song_ids:
            song = Song.query.get(song_id)
            if song:
                song.album_id = album.id
                album_name = Album.query.get(album.id).name
                song.album_name = album_name
                db.session.commit()


        return redirect(url_for('album', album_id=album.id))
    print(current_user.id)

    
    songs = Song.query.filter(Song.album_id == album_id).all()
    songlist = [{'id': song.id, 'title': song.title, 'artist': song.artist, 'song_icon': song.song_icon, 'file_path': song.file_path, 'genre':song.genre} for song in songs]

  

    return render_template('album.html', album=album, songs=songs, is_creator=is_creator, songlist=songlist, current_user=current_user)

#admin routes
@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['admin_username']
        password = request.form['admin_password']

        
        
        if username == 'admin' and password == 'admin':
            
            session['is_admin'] = True
            print('Admin login successful!', 'success')
            return redirect(url_for('admin_dashboard'))

        print('Invalid admin credentials. Please try again.', 'error')

    return render_template('admin_login.html')


def admin_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        is_admin = session.get('is_admin', False)        
        
        if  not is_admin:
            
            return redirect(url_for('login'))  
            
        return func(*args, **kwargs)
    return decorated_view


@app.route('/admin/admin-logout')
@admin_required
def admin_logout():
    
    session['is_admin'] = False 
    return render_template('login.html')

@app.route('/admin/admin-dashboard', methods=['GET', 'POST'])
@admin_required
def admin_dashboard():
    
    log_file_path = os.path.join(app.static_folder, 'logs/app.log')
    songs = Song.query.all()
    users = user.query.all()
    creators = creator.query.all()
    comment_stats = []
    playlist_stats = []
    user_stats = get_stats("user")
    creator_stats = []

    for usr in users:        
        user_albums = Album.query.filter_by(creator_id=usr.id).all()
        for album in user_albums:           
            album_songs = Song.query.filter_by(album_id=album.id).all()
            creator_stats.append({
                'user_id': usr.id,
                'album_id': album.id,
                'album_name': album.name,
                'album_songs': album_songs,
            })


    for usr in users:
        user_playlists = Playlist.query.filter_by(creator_id=usr.id).all()
        for playlist in user_playlists:
            playlist_songs = get_songs_in_playlist(playlist.id)
            playlist_stats.append({
                'user_id': usr.id,
                'playlist_id': playlist.id,
                'playlist_title': playlist.name,
                'playlist_songs': playlist_songs,
            })
    
    for song in songs:
        song_id = song.id
        song_comments = get_song_comments(song_id)
        ratings = Rating.query.filter_by(song_id=song_id).all()
        comment_stats.append({
            'song_id': song_id,
            'title': song.title,
            'comments': song_comments,
            'ratings': ratings,
        })

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'delete_comment':
            comment_id = int(request.form.get('comment_id'))            
            Comment.query.filter_by(id=comment_id).delete()            
            db.session.commit()            
            return redirect(url_for('admin_dashboard'))
        
        elif action == 'execute_query':
            sql_query = request.form.get('sql_query', '')

            try:
                result = db.session.execute(text(sql_query))  
                results = result.fetchall()
                print("executed successfully")
            except Exception as e:
                error_message = f"Error executing SQL query: {str(e)}"
                print(error_message)  
              

    with open(log_file_path, 'r') as log_file:
        logs = log_file.readlines()

    return render_template('admin_dashboard.html', logs=logs, songs=songs, users=users, creators=creators, playlist_stats=playlist_stats,
                           user_stats=user_stats, comment_stats=comment_stats, creator_stats=creator_stats, result=results if 'results' in locals() else None)