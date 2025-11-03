# app/main.py
from flask import Blueprint, redirect, url_for

bp = Blueprint('main', __name__)


@bp.route('/')
def index():
    """根路径，重定向到首页"""
    return redirect(url_for('auth.login'))
