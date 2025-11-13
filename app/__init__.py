# app/__init__.py
from flask import Flask, redirect, url_for
from flask_login import LoginManager
from config import Config


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # 初始化扩展，创建数据库
    from app.models import db
    db.init_app(app)

    """
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))
    从会话恢复用户：当用户已经登录，Flask-Login 通过会话中的用户ID调用此函数
    返回用户对象：根据用户ID从数据库查询并返回对应的 User 对象
    维持登录状态：确保用户在会话期间保持登录状态

    在auth.py中@login_required：定义"哪些页面需要登录" 

    LoginManager：定义"未登录时如何处理"

    跳转到哪里 (login_view)

    显示什么消息 (login_message)

    如何加载用户 (user_loader)
    """
    # 初始化和配置登录管理器
    login_manager = LoginManager()
    login_manager.init_app(app)  # 将其与 Flask 应用关联
    login_manager.login_view = 'auth.login'  # 当用户访问需要登录的页面时，重定向到哪个路由，auth.login表示重定向到 auth 蓝图下的 login 路由
    login_manager.login_message = '请先登录'  # 重定向时显示的提示消息
    login_manager.login_message_category = 'info'

    # 用户加载回调函数
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))

    # 注册蓝图
    from app.auth import bp as auth_bp  # 导入认证蓝图
    app.register_blueprint(auth_bp)
    from app.main import bp as main_bp  # 导入主蓝图
    app.register_blueprint(main_bp)
    from app.admin.routes import bp as admin_bp  # 导入admin蓝图
    app.register_blueprint(admin_bp)
    from app.teacher.routes import bp as teacher_bp  # 导入教师蓝图
    app.register_blueprint(teacher_bp)
    return app
