# app/models.py
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
import enum

db = SQLAlchemy()


class RoleType(enum.Enum):
    """
    主要作用：
        定义系统支持的固定角色类型
        确保角色数据的一致性 - 只能使用预定义的角色
        防止无效角色值进入数据库
    """
    ADMIN = "admin"
    TEACHER = "teacher"
    STUDENT = "student"
    CLASS_TEACHER = "class_teacher"  # 确保与需求文档中的班主任角色一致


"""
↓用户表需要身份认证
用户体系（继承UserMixin）
├── User (基类)
├── Student 
├── Teacher
└── Admin
"""


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    # index=True: 创建数据库索引，加速基于用户名的查询
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.Enum(RoleType), nullable=False)
    # db.Enum(RoleType): 枚举类型字段，只能存储预定义的角色值
    # nullable=False: 每个用户必须分配一个角色
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    # default=db.func.current_timestamp(): 默认值使用数据库的当前时间戳,创建记录时自动设置为当前时间,不需要手动赋值

    type = db.Column(db.String(20))  # 继承鉴别器字段

    __mapper_args__ = {
        'polymorphic_identity': 'user',  # 当前类的身份标识
        'polymorphic_on': type  # 告诉SQLAlchemy：用type字段来判断对象类型从而创建正确的对象
    }

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Student(User):
    __tablename__ = 'students'

    id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    # 外键是一个表中的字段，它引用另一个表的主键，用于建立表之间的关系。这个外键指向 users.id，建立继承关系。
    student_id = db.Column(db.String(20), unique=True, nullable=False, index=True)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'))
    # 这个外键指向 classes.id，建立班级关系
    major = db.Column(db.String(100))

    grades = db.relationship('Grade', back_populates='student', lazy='dynamic')
    """
    目的：建立学生与成绩的一对多关系。一个学生可以有多个成绩记录，一个成绩记录只属于一个学生
    'Grade'：目标模型类名
    back_populates='student'：在 Grade 模型中也要定义对应的关系
    lazy='dynamic'：返回查询对象而不是直接结果，可以继续过滤
    """
    class_ = db.relationship('Class', back_populates='students')
    """
    目的：建立学生与班级的多对一关系。一个学生属于一个班级，一个班级可以有多个学生
    'Class'：目标模型类名
    back_populates='students'：在 Class 模型中定义反向关系
    lazy 未指定：默认是 'select'，自动加载关联对象
    """

    __mapper_args__ = {
        'polymorphic_identity': 'student',
    }


class Teacher(User):
    __tablename__ = 'teachers'

    id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    teacher_id = db.Column(db.String(20), unique=True, nullable=False, index=True)
    department = db.Column(db.String(100))  # 部门
    title = db.Column(db.String(50))  # 职称

    courses = db.relationship('Course', secondary='teacher_course', back_populates='teachers')
    """
    目的：一个教师可以教授多门课程，一门课程可以由多个教师教授
    secondary='teacher_course'：指定多对多关联表
    back_populates='teachers'：在 Course 模型中定义反向关系
    """
    grades = db.relationship('Grade', back_populates='teacher', lazy='dynamic')
    # 一个教师可以录入多个成绩记录
    managed_classes = db.relationship('Class', back_populates='class_teacher')
    # 一个教师可以担任多个班级的班主任
    __mapper_args__ = {
        'polymorphic_identity': 'teacher',
    }


class Admin(User):
    __tablename__ = 'admins'

    id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    admin_id = db.Column(db.String(20), unique=True, nullable=False, index=True)

    __mapper_args__ = {
        'polymorphic_identity': 'admin',
    }


"""
↓业务表不需要身份认证
业务数据体系（只继承db.Model）
├── Course
├── Class  
├── Grade
├── teacher_course (关联表)
└── GradeModificationLog
"""


class Course(db.Model):
    __tablename__ = 'courses'

    id = db.Column(db.Integer, primary_key=True)
    course_code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    course_name = db.Column(db.String(100), nullable=False)
    credits = db.Column(db.Integer, nullable=False)
    hours = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text)

    teachers = db.relationship('Teacher', secondary='teacher_course', back_populates='courses')
    grades = db.relationship('Grade', back_populates='course', lazy='dynamic')


class Class(db.Model):
    __tablename__ = 'classes'

    id = db.Column(db.Integer, primary_key=True)
    class_code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    class_name = db.Column(db.String(100), nullable=False)
    major = db.Column(db.String(100))

    students = db.relationship('Student', back_populates='class_', lazy='dynamic')
    class_teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'))
    class_teacher = db.relationship('Teacher', back_populates='managed_classes')


class Grade(db.Model):
    __tablename__ = 'grades'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=False)
    score = db.Column(db.Float, nullable=False)
    semester = db.Column(db.String(20), nullable=False)
    academic_year = db.Column(db.String(10), nullable=False)
    is_makeup = db.Column(db.Boolean, default=False)
    is_locked = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    student = db.relationship('Student', back_populates='grades')
    course = db.relationship('Course', back_populates='grades')
    teacher = db.relationship('Teacher', back_populates='grades')


teacher_course = db.Table('teacher_course',
                          db.Column('teacher_id', db.Integer, db.ForeignKey('teachers.id'), primary_key=True),
                          db.Column('course_id', db.Integer, db.ForeignKey('courses.id'), primary_key=True),
                          db.Column('assigned_at', db.DateTime, default=db.func.current_timestamp())
                          )


class GradeModificationLog(db.Model):
    __tablename__ = 'grade_modification_logs'

    id = db.Column(db.Integer, primary_key=True)
    grade_id = db.Column(db.Integer, db.ForeignKey('grades.id'), nullable=False)
    previous_score = db.Column(db.Float, nullable=False)
    new_score = db.Column(db.Float, nullable=False)
    modified_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    reason = db.Column(db.Text)
    modified_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    grade = db.relationship('Grade')
    modifier = db.relationship('User')
