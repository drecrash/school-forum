from flask import Flask, render_template, url_for, redirect, request, jsonify
from flask_socketio import SocketIO
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import and_
from flask_uploads import UploadSet, IMAGES, configure_uploads
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate

app = Flask(__name__)
app.secret_key = "%23144141*(043248fsnsf)"
socketio = SocketIO(app)
#
app.jinja_env.add_extension('jinja2.ext.loopcontrols')

login_manager = LoginManager(app)


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dump.db'

app.config['SQLALCHEMY_BINDS'] = {'users': 'sqlite:///users.db',
                                  'threads': 'sqlite:///threads.db',
                                  'comments': 'sqlite:///comments.db',
                                  'update_log': 'sqlite:///updates.db',
                                  'tags': 'sqlite:///tags.db'}

app.config['UPLOADED_PHOTOS_DEST'] = '/static/thread-images'

photos = UploadSet('photos', IMAGES)
configure_uploads(app, photos)

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[],
    storage_uri="memory://",
)

db = SQLAlchemy(app)
migrate = Migrate(app, db)