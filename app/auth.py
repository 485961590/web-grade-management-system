# app/auth.py
from flask import render_template, redirect, url_for, flash, request, Blueprint
from flask_login import login_user, logout_user, login_required, current_user
from app.models import db, User, RoleType
from app.forms import LoginForm, ChangePasswordForm, ProfileForm

bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/')
@login_required
def index():
    return render_template('auth/index.html')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('auth.index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        if user and user.check_password(form.password.data):
            login_user(user)
            flash('登录成功！', 'success')
            next_page = request.args.get('next')

            # 基于角色的重定向
            if user.role == RoleType.ADMIN:
                return redirect(next_page or url_for('admin.dashboard'))
            elif user.role == RoleType.TEACHER:
                return redirect(next_page or url_for('teacher.dashboard'))
            elif user.role == RoleType.STUDENT:
                return redirect(next_page or url_for('student.grades'))
            else:
                return redirect(next_page or url_for('auth.index'))
        else:
            flash('用户名或密码错误', 'error')

    return render_template('auth/login.html', form=form)


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('您已成功退出登录', 'success')
    return redirect(url_for('auth.login'))


@bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.check_password(form.current_password.data):
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash('密码修改成功', 'success')
            return redirect(url_for('auth.index'))
        else:
            flash('当前密码错误', 'error')

    return render_template('auth/change_password.html', form=form)


@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm()
    if form.validate_on_submit():
        current_user.email = form.email.data
        current_user.phone = form.phone.data
        db.session.commit()
        flash('个人信息更新成功', 'success')
        return redirect(url_for('auth.index'))

    # 预填充表单数据
    form.email.data = current_user.email
    form.phone.data = current_user.phone

    return render_template('auth/profile.html', form=form)
