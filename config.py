# config.py
import os


class Config:
    """基础配置类"""
    # 数据库配置 - MySQL
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:root@127.0.0.1:3306/grade_management'
    # 关闭SQLAlchemy事件系统
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # 安全密钥（用于会话等）
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    # 密码加密轮数
    BCRYPT_ROUNDS = 12


# 创建配置实例
config = Config()
