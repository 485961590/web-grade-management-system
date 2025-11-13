from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user
from app.models import RoleType

from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user
from app.models import RoleType


def teacher_required(f):
    """教师和班主任权限验证"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('请先登录', 'error')
            return redirect(url_for('auth.login'))

        # 允许教师和班主任访问
        if current_user.role not in [RoleType.TEACHER, RoleType.CLASS_TEACHER]:
            flash('无权访问教师页面', 'error')
            return redirect(url_for('main.index'))

        return f(*args, **kwargs)

    return decorated_function
