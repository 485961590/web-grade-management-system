# app/__init__.py
from flask import Flask
from flask_login import LoginManager
from config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # 初始化扩展
    from app.models import db
    db.init_app(app)

    # 初始化登录管理器
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message = '请先登录'

    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))

    return app