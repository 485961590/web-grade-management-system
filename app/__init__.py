from flask import Flask
from config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # 初始化扩展
    from app.models import db
    db.init_app(app)

    return app