from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user
from app.models import RoleType


def student_required(f):
    """学生权限验证"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('请先登录', 'error')
            return redirect(url_for('auth.login'))

        if current_user.role != RoleType.STUDENT:
            flash('无权访问学生页面', 'error')
            return redirect(url_for('main.index'))

        return f(*args, **kwargs)

    return decorated_function