from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user


def admin_required(f):
    """要求用户必须是管理员的装饰器"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('请先登录', 'error')
            return redirect(url_for('auth.login'))

        if current_user.role.value != 'admin':
            flash('权限不足，仅管理员可访问此页面', 'error')
            return redirect(url_for('auth.index'))

        return f(*args, **kwargs)

    return decorated_function
