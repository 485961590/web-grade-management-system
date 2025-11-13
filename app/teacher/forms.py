from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField, SelectField, BooleanField, PasswordField
from wtforms.validators import DataRequired, Length, NumberRange, Optional, EqualTo
from app.models import Student


class GradeForm(FlaskForm):
    """成绩表单"""
    student_id = SelectField('选择学生', coerce=int, validators=[DataRequired()])
    course_id = SelectField('选择课程', coerce=int, validators=[DataRequired()])
    score = IntegerField('成绩', validators=[DataRequired(), NumberRange(min=0, max=100)])
    semester = SelectField('学期', choices=[
        ('2024-2025-1', '2024-2025学年第一学期'),
        ('2024-2025-2', '2024-2025学年第二学期'),
        ('2023-2024-1', '2023-2024学年第一学期'),
        ('2023-2024-2', '2023-2024学年第二学期'),
    ], validators=[DataRequired()])
    academic_year = StringField('学年', validators=[DataRequired()], default='2024-2025')
    is_makeup = BooleanField('补考成绩')
    submit = SubmitField('保存')

    def __init__(self, *args, **kwargs):
        super(GradeForm, self).__init__(*args, **kwargs)
        # 动态加载学生
        self.student_id.choices = [(s.id, f"{s.student_id} - {s.username}")
                                  for s in Student.query.order_by(Student.student_id).all()]


class GradeSearchForm(FlaskForm):
    """成绩搜索表单"""
    search = StringField('搜索学生', validators=[Optional()])
    course_id = SelectField('课程筛选', coerce=int, validators=[Optional()])
    semester = SelectField('学期筛选', choices=[
        ('', '所有学期'),
        ('2024-2025-1', '2024-2025-1'),
        ('2024-2025-2', '2024-2025-2'),
        ('2023-2024-1', '2023-2024-1'),
        ('2023-2024-2', '2023-2024-2'),
    ], validators=[Optional()])
    submit = SubmitField('搜索')


class TeacherProfileForm(FlaskForm):
    """教师个人信息表单"""
    email = StringField('邮箱', validators=[Optional()])
    phone = StringField('电话', validators=[Optional(), Length(max=20)])
    new_password = PasswordField('新密码', validators=[Optional(), Length(min=6)])
    confirm_password = PasswordField('确认密码', validators=[
        Optional(),
        EqualTo('new_password', message='密码不一致')
    ])
    submit = SubmitField('更新信息')