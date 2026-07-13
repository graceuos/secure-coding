import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)

    # 보안 포인트 1: SECRET_KEY는 세션 암호화, CSRF 토큰 생성에 쓰입니다.
    # 실제 배포 시에는 코드에 직접 쓰지 않고 환경변수로 관리해야 합니다.
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-temporary-key-change-me')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///market.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # 보안 포인트 2: 세션 쿠키를 JS로 못 읽게 막고(HttpOnly), 자바스크립트 접근 차단
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from app.auth import auth_bp
    app.register_blueprint(auth_bp)

    with app.app_context():
        db.create_all()

    return app
