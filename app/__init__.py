from flask import Flask
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

from app.config import Config


bcrypt = Bcrypt()
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    load_dotenv()

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    from app.routes import auth_bp, main_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    with app.app_context():
        db.create_all()

    return app
