# app/forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, EmailField, TelField
from wtforms.validators import DataRequired, Length, EqualTo


class LoginForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired()])
    password = PasswordField('密码', validators=[DataRequired()])
    submit = SubmitField('登录')


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('当前密码', validators=[DataRequired()])
    new_password = PasswordField('新密码', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('确认密码', validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('修改密码')


class ProfileForm(FlaskForm):
    email = EmailField('邮箱')
    phone = TelField('电话')
    submit = SubmitField('更新信息')
