from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField, TextAreaField, SelectField, SelectMultipleField, \
    BooleanField
from wtforms.validators import DataRequired, Length, NumberRange, Optional
from app.models import Class, Course, Teacher, Student


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


class ClassForm(FlaskForm):
    """班级信息表单"""
    class_code = StringField('班级代码', validators=[DataRequired(), Length(max=20)])
    class_name = StringField('班级名称', validators=[DataRequired(), Length(max=100)])
    major = StringField('专业', validators=[DataRequired(), Length(max=100)])
    class_teacher_id = SelectField('班主任', coerce=int, validators=[Optional()])
    submit = SubmitField('保存')

    def __init__(self, *args, **kwargs):
        super(ClassForm, self).__init__(*args, **kwargs)
        # 动态加载教师选项
        self.class_teacher_id.choices = [(0, '未分配')] + [(t.id, f"{t.username} ({t.teacher_id})")
                                                           for t in Teacher.query.order_by(Teacher.username).all()]


class GradeForm(FlaskForm):
    """成绩信息表单"""
    student_id = SelectField('学生', coerce=int, validators=[DataRequired()])
    course_id = SelectField('课程', coerce=int, validators=[DataRequired()])
    teacher_id = SelectField('授课教师', coerce=int, validators=[DataRequired()])
    score = IntegerField('成绩', validators=[DataRequired(), NumberRange(min=0, max=100)])
    semester = SelectField('学期', choices=[
        ('2024-2025-1', '2024-2025学年第一学期'),
        ('2024-2025-2', '2024-2025学年第二学期'),
        ('2023-2024-1', '2023-2024学年第一学期'),
        ('2023-2024-2', '2023-2024学年第二学期'),
        ('2022-2023-1', '2022-2023学年第一学期'),
        ('2022-2023-2', '2022-2023学年第二学期')
    ], validators=[DataRequired()])
    academic_year = StringField('学年', validators=[DataRequired(), Length(max=10)],
                                default='2024-2025')
    is_makeup = BooleanField('补考成绩')
    submit = SubmitField('保存')

    def __init__(self, *args, **kwargs):
        super(GradeForm, self).__init__(*args, **kwargs)
        # 动态加载学生选项
        self.student_id.choices = [(s.id, f"{s.username} ({s.student_id})")
                                   for s in Student.query.order_by(Student.student_id).all()]
        # 动态加载课程选项
        self.course_id.choices = [(c.id, f"{c.course_code} - {c.course_name}")
                                  for c in Course.query.order_by(Course.course_code).all()]
        # 动态加载教师选项
        self.teacher_id.choices = [(t.id, f"{t.username} ({t.teacher_id})")
                                   for t in Teacher.query.order_by(Teacher.username).all()]


class GradeSearchForm(FlaskForm):
    """成绩搜索表单"""
    student_search = StringField('学生姓名/学号', validators=[Optional()])
    course_search = StringField('课程名称/代码', validators=[Optional()])
    semester_filter = SelectField('学期', choices=[
        ('', '所有学期'),
        ('2024-2025-1', '2024-2025学年第一学期'),
        ('2024-2025-2', '2024-2025学年第二学期'),
        ('2023-2024-1', '2023-2024学年第一学期'),
        ('2023-2024-2', '2023-2024学年第二学期')
    ], validators=[Optional()])
    submit = SubmitField('搜索')
