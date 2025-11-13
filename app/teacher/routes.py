from flask import render_template, redirect, url_for, flash, request, Blueprint
from flask_login import login_required, current_user
from sqlalchemy import or_, and_

from app.models import db, Course, Grade, Student
from app.teacher.forms import GradeForm, GradeSearchForm, TeacherProfileForm
from app.teacher.decorators import teacher_required

bp = Blueprint('teacher', __name__, url_prefix='/teacher')


@bp.route('/')
@login_required
@teacher_required
def dashboard():
    """教师仪表板"""
    teacher = current_user

    # 获取教师统计数据
    total_courses = len(teacher.courses)
    total_grades = Grade.query.filter_by(teacher_id=teacher.id).count()

    # 获取最近录入的成绩
    recent_grades = Grade.query.filter_by(teacher_id=teacher.id) \
        .order_by(Grade.created_at.desc()) \
        .limit(5).all()

    # 获取各课程成绩统计
    course_stats = []
    for course in teacher.courses:
        course_grades = Grade.query.filter_by(
            teacher_id=teacher.id,
            course_id=course.id
        ).all()

        if course_grades:
            avg_score = sum(grade.score for grade in course_grades) / len(course_grades)
            course_stats.append({
                'course': course,
                'count': len(course_grades),
                'avg_score': round(avg_score, 1)
            })

    return render_template('teacher/dashboard.html',
                           total_courses=total_courses,
                           total_grades=total_grades,
                           recent_grades=recent_grades,
                           course_stats=course_stats)


@bp.route('/courses')
@login_required
@teacher_required
def courses():
    """我的课程"""
    teacher = current_user
    return render_template('teacher/courses.html', courses=teacher.courses)


@bp.route('/grades')
@login_required
@teacher_required
def grades():
    """成绩管理"""
    page = request.args.get('page', 1, type=int)
    per_page = 10

    # 基础查询 - 只显示当前教师的成绩
    query = Grade.query.filter_by(teacher_id=current_user.id)

    # 搜索过滤
    search = request.args.get('search', '')
    course_id = request.args.get('course_id', type=int)
    semester = request.args.get('semester', '')

    if search:
        query = query.join(Student).filter(
            or_(
                Student.username.ilike(f'%{search}%'),
                Student.student_id.ilike(f'%{search}%')
            )
        )

    if course_id:
        query = query.filter_by(course_id=course_id)

    if semester:
        query = query.filter_by(semester=semester)

    grades = query.order_by(Grade.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return render_template('teacher/grades.html',
                           grades=grades,
                           search=search,
                           course_id=course_id,
                           semester=semester)


@bp.route('/grades/create', methods=['GET', 'POST'])
@login_required
@teacher_required
def create_grade():
    """录入成绩"""
    form = GradeForm()

    # 只显示当前教师教授的课程
    form.course_id.choices = [(c.id, f"{c.course_code} - {c.course_name}")
                              for c in current_user.courses]

    if form.validate_on_submit():
        # 检查是否已存在相同记录
        existing = Grade.query.filter_by(
            student_id=form.student_id.data,
            course_id=form.course_id.data,
            semester=form.semester.data
        ).first()

        if existing:
            flash('该学生在此课程和学期下已有成绩记录', 'error')
        else:
            grade = Grade(
                student_id=form.student_id.data,
                course_id=form.course_id.data,
                teacher_id=current_user.id,
                score=form.score.data,
                semester=form.semester.data,
                academic_year=form.academic_year.data,
                is_makeup=form.is_makeup.data
            )

            db.session.add(grade)
            db.session.commit()
            flash('成绩录入成功！', 'success')
            return redirect(url_for('teacher.grades'))

    return render_template('teacher/create_grade.html', form=form)


@bp.route('/grades/<int:grade_id>/edit', methods=['GET', 'POST'])
@login_required
@teacher_required
def edit_grade(grade_id):
    """编辑成绩"""
    grade = Grade.query.filter_by(id=grade_id, teacher_id=current_user.id).first_or_404()
    form = GradeForm(obj=grade)

    # 只显示当前教师教授的课程
    form.course_id.choices = [(c.id, f"{c.course_code} - {c.course_name}")
                              for c in current_user.courses]

    if form.validate_on_submit():
        # 检查冲突（排除当前记录）
        existing = Grade.query.filter(
            Grade.student_id == form.student_id.data,
            Grade.course_id == form.course_id.data,
            Grade.semester == form.semester.data,
            Grade.id != grade_id
        ).first()

        if existing:
            flash('该学生在此课程和学期下已有其他成绩记录', 'error')
        else:
            form.populate_obj(grade)
            db.session.commit()
            flash('成绩更新成功！', 'success')
            return redirect(url_for('teacher.grades'))

    return render_template('teacher/edit_grade.html', form=form, grade=grade)


@bp.route('/grades/<int:grade_id>/delete', methods=['POST'])
@login_required
@teacher_required
def delete_grade(grade_id):
    """删除成绩"""
    grade = Grade.query.filter_by(id=grade_id, teacher_id=current_user.id).first_or_404()

    db.session.delete(grade)
    db.session.commit()
    flash('成绩删除成功！', 'success')

    return redirect(url_for('teacher.grades'))


@bp.route('/students')
@login_required
@teacher_required
def students():
    """学生查询"""
    page = request.args.get('page', 1, type=int)
    per_page = 15
    search = request.args.get('search', '')

    query = Student.query

    if search:
        query = query.filter(
            or_(
                Student.username.ilike(f'%{search}%'),
                Student.student_id.ilike(f'%{search}%')
            )
        )

    students = query.order_by(Student.student_id).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return render_template('teacher/students.html', students=students, search=search)


@bp.route('/profile', methods=['GET', 'POST'])
@login_required
@teacher_required
def profile():
    """个人信息"""
    form = TeacherProfileForm(obj=current_user)

    if form.validate_on_submit():
        current_user.email = form.email.data
        current_user.phone = form.phone.data

        # 更新密码（如果提供了新密码）
        if form.new_password.data:
            current_user.set_password(form.new_password.data)
            flash('密码更新成功！', 'success')

        db.session.commit()
        flash('个人信息更新成功！', 'success')
        return redirect(url_for('teacher.profile'))

    return render_template('teacher/profile.html', form=form)