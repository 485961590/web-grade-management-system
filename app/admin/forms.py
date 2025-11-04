from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Length, NumberRange, Optional
from app.models import Class


class CourseForm(FlaskForm):
    """课程信息表单"""
    course_code = StringField('课程代码', validators=[DataRequired(), Length(max=20)])
    course_name = StringField('课程名称', validators=[DataRequired(), Length(max=100)])
    credits = IntegerField('学分', validators=[DataRequired(), NumberRange(min=1, max=10)])
    hours = IntegerField('学时', validators=[DataRequired(), NumberRange(min=1, max=200)])
    description = TextAreaField('课程描述', validators=[Optional(), Length(max=500)])
    submit = SubmitField('保存')


class TeacherForm(FlaskForm):
    """教师信息表单"""
    teacher_id = StringField('教师工号', validators=[DataRequired(), Length(max=20)])
    username = StringField('用户名', validators=[DataRequired(), Length(max=64)])
    email = StringField('邮箱', validators=[Optional()])
    phone = StringField('电话', validators=[Optional(), Length(max=20)])
    department = StringField('院系', validators=[DataRequired(), Length(max=100)])
    title = StringField('职称', validators=[Optional(), Length(max=50)])
    submit = SubmitField('保存')


class StudentForm(FlaskForm):
    """学生信息表单"""
    student_id = StringField('学号', validators=[DataRequired(), Length(max=20)])
    username = StringField('用户名', validators=[DataRequired(), Length(max=64)])
    email = StringField('邮箱', validators=[Optional()])
    phone = StringField('电话', validators=[Optional(), Length(max=20)])
    class_id = SelectField('班级', coerce=int, validators=[DataRequired()])
    major = StringField('专业', validators=[DataRequired(), Length(max=100)])
    submit = SubmitField('保存')

    def __init__(self, *args, **kwargs):
        super(StudentForm, self).__init__(*args, **kwargs)
        # 动态加载班级选项
        self.class_id.choices = [(c.id, f"{c.class_name} ({c.class_code})")
                                 for c in Class.query.order_by(Class.class_name).all()]