from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField, TextAreaField, SelectField, SelectMultipleField
from wtforms.validators import DataRequired, Length, NumberRange, Optional
from app.models import Class, Course


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


class TeacherCourseForm(FlaskForm):
    """教师课程绑定表单"""
    course_ids = SelectMultipleField('选择课程', coerce=int, validators=[DataRequired()])
    submit = SubmitField('绑定课程')

    def __init__(self, *args, **kwargs):
        super(TeacherCourseForm, self).__init__(*args, **kwargs)  # 这里要改为 TeacherCourseForm
        # 动态加载课程选项
        self.course_ids.choices = [(c.id, f"{c.course_code} - {c.course_name}")
                                   for c in Course.query.order_by(Course.course_code).all()]
