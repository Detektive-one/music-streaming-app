from flask import Flask
from app.models import db, user
from flask_login import LoginManager
import logging
from datetime import datetime, timezone, timedelta


ist = timezone(timedelta(hours=5, minutes=30))

log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
log_formatter.converter = lambda *args: datetime.now(ist).timetuple()
file_handler = logging.FileHandler('static/logs/app.log')
file_handler.setFormatter(log_formatter)


app = Flask(__name__,  static_folder='../static', template_folder='../templates')


app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)
app.logger.removeHandler(app.logger.handlers[0])


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db.init_app(app)


login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    
    login_user = user.query.get(int(user_id))
    return login_user        


with app.app_context():
    db.create_all()



app.secret_key = 'random32bits'

from app import routes


