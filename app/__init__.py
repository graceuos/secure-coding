import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_socketio import SocketIO

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
socketio = SocketIO()

def create_app():
    app = Flask(__name__)

    # 보안 포인트 1: SECRET_KEY는 세션 암호화, CSRF 토큰 생성에 쓰입니다.
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-temporary-key-change-me')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///market.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # 보안 포인트 2: 세션 쿠키를 JS로 못 읽게 막고(HttpOnly)
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    csrf.init_app(app)
    socketio.init_app(app)

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from app.auth import auth_bp
    app.register_blueprint(auth_bp)

    from app.products import products_bp
    app.register_blueprint(products_bp)

    from app.chat import chat_bp
    app.register_blueprint(chat_bp)

    with app.app_context():
        db.create_all()

    return app
