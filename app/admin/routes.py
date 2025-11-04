from flask import render_template, redirect, url_for, flash, request, Blueprint
from flask_login import login_required, current_user
from sqlalchemy import or_

from app.models import db, Course, Teacher, Student, Class, User, RoleType, Grade
from app.admin.forms import CourseForm, TeacherForm, StudentForm, TeacherCourseForm
from app.admin.decorators import admin_required

bp = Blueprint('admin', __name__, url_prefix='/admin')


@bp.route('/')
@login_required
@admin_required
def dashboard():
    """管理员仪表板"""
    # 获取统计数据
    stats = {
        'total_courses': Course.query.count(),
        'total_teachers': Teacher.query.count(),
        'total_students': Student.query.count(),
        'total_classes': Class.query.count(),
        'total_grades': Grade.query.count(),
        'recent_grades': Grade.query.order_by(Grade.created_at.desc()).limit(10).all()
    }
    return render_template('admin/dashboard.html', stats=stats)


# ==================== 课程管理 ====================

@bp.route('/courses')
@login_required
@admin_required
def course_list():
    """课程列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('search', '')
    sort = request.args.get('sort', 'code')  # 默认按课程代码排序

    # 构建查询
    query = Course.query

    # 搜索功能
    if search:
        query = query.filter(
            db.or_(
                Course.course_code.ilike(f'%{search}%'),
                Course.course_name.ilike(f'%{search}%')
            )
        )

    # 排序功能
    if sort == 'name':
        query = query.order_by(Course.course_name)
    elif sort == 'credits':
        query = query.order_by(Course.credits.desc())
    else:  # 默认按课程代码排序
        query = query.order_by(Course.course_code)

    # 分页
    courses = query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )

    return render_template('admin/courses/list.html', courses=courses)


@bp.route('/courses/create', methods=['GET', 'POST'])
@login_required
@admin_required
def course_create():
    """创建课程"""
    form = CourseForm()

    if form.validate_on_submit():
        # 检查课程代码是否已存在
        existing_course = Course.query.filter_by(course_code=form.course_code.data).first()
        if existing_course:
            flash('课程代码已存在', 'error')
            return render_template('admin/courses/create.html', form=form)

        course = Course(
            course_code=form.course_code.data,
            course_name=form.course_name.data,
            credits=form.credits.data,
            hours=form.hours.data,
            description=form.description.data
        )

        db.session.add(course)
        db.session.commit()

        flash(f'课程 "{form.course_name.data}" 创建成功', 'success')
        return redirect(url_for('admin.course_list'))

    return render_template('admin/courses/create.html', form=form)


@bp.route('/courses/<int:course_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def course_edit(course_id):
    """编辑课程"""
    course = Course.query.get_or_404(course_id)
    form = CourseForm(obj=course)

    if form.validate_on_submit():
        # 检查课程代码是否与其他课程冲突
        existing_course = Course.query.filter(
            Course.course_code == form.course_code.data,
            Course.id != course_id
        ).first()

        if existing_course:
            flash('课程代码已存在', 'error')
            return render_template('admin/courses/edit.html', form=form, course=course)

        course.course_code = form.course_code.data
        course.course_name = form.course_name.data
        course.credits = form.credits.data
        course.hours = form.hours.data
        course.description = form.description.data

        db.session.commit()
        flash(f'课程 "{form.course_name.data}" 更新成功', 'success')
        return redirect(url_for('admin.course_list'))

    return render_template('admin/courses/edit.html', form=form, course=course)


@bp.route('/courses/<int:course_id>/delete', methods=['POST'])
@login_required
@admin_required
def course_delete(course_id):
    """删除课程"""
    course = Course.query.get_or_404(course_id)

    # 检查是否有成绩关联
    if course.grades.count() > 0:
        flash('无法删除该课程，因为已有成绩记录关联', 'error')
        return redirect(url_for('admin.course_list'))

    db.session.delete(course)
    db.session.commit()

    flash(f'课程 "{course.course_name}" 已删除', 'success')
    return redirect(url_for('admin.course_list'))


# ==================== 教师管理 ====================

@bp.route('/teachers')
@login_required
@admin_required
def teacher_list():
    """教师列表"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    search = request.args.get('search', '')
    department = request.args.get('department', '')

    # 构建查询
    query = Teacher.query

    # 搜索功能
    if search:
        query = query.filter(
            db.or_(
                Teacher.teacher_id.ilike(f'%{search}%'),
                Teacher.username.ilike(f'%{search}%'),
                Teacher.department.ilike(f'%{search}%')
            )
        )

    # 院系筛选
    if department:
        query = query.filter(Teacher.department == department)

    teachers = query.order_by(Teacher.teacher_id).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return render_template('admin/teachers/list.html', teachers=teachers)


@bp.route('/teachers/create', methods=['GET', 'POST'])
@login_required
@admin_required
def teacher_create():
    """创建教师账户"""
    form = TeacherForm()

    if form.validate_on_submit():
        # 检查用户名和教师工号是否已存在
        if User.query.filter_by(username=form.username.data).first():
            flash('用户名已存在', 'error')
            return render_template('admin/teachers/create.html', form=form)

        if Teacher.query.filter_by(teacher_id=form.teacher_id.data).first():
            flash('教师工号已存在', 'error')
            return render_template('admin/teachers/create.html', form=form)

        # 创建教师用户
        teacher = Teacher(
            username=form.username.data,
            teacher_id=form.teacher_id.data,
            email=form.email.data,
            phone=form.phone.data,
            department=form.department.data,
            title=form.title.data,
            role=RoleType.TEACHER
        )

        # 设置初始密码（工号后6位）
        initial_password = form.teacher_id.data[-6:] if len(form.teacher_id.data) >= 6 else form.teacher_id.data
        teacher.set_password(initial_password)

        db.session.add(teacher)
        db.session.commit()

        flash(f'教师 "{form.username.data}" 创建成功，初始密码为: {initial_password}', 'success')
        return redirect(url_for('admin.teacher_list'))

    return render_template('admin/teachers/create.html', form=form)


@bp.route('/teachers/<int:teacher_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def teacher_edit(teacher_id):
    """编辑教师信息"""
    teacher = Teacher.query.get_or_404(teacher_id)
    form = TeacherForm(obj=teacher)

    if form.validate_on_submit():
        # 检查用户名是否与其他用户冲突
        existing_user = User.query.filter(
            User.username == form.username.data,
            User.id != teacher_id
        ).first()

        if existing_user:
            flash('用户名已存在', 'error')
            return render_template('admin/teachers/edit.html', form=form, teacher=teacher)

        # 检查教师工号是否与其他教师冲突
        existing_teacher = Teacher.query.filter(
            Teacher.teacher_id == form.teacher_id.data,
            Teacher.id != teacher_id
        ).first()

        if existing_teacher:
            flash('教师工号已存在', 'error')
            return render_template('admin/teachers/edit.html', form=form, teacher=teacher)

        teacher.username = form.username.data
        teacher.teacher_id = form.teacher_id.data
        teacher.email = form.email.data
        teacher.phone = form.phone.data
        teacher.department = form.department.data
        teacher.title = form.title.data

        db.session.commit()
        flash(f'教师 "{form.username.data}" 更新成功', 'success')
        return redirect(url_for('admin.teacher_list'))

    return render_template('admin/teachers/edit.html', form=form, teacher=teacher)


@bp.route('/teachers/<int:teacher_id>/reset-password', methods=['POST'])
@login_required
@admin_required
def teacher_reset_password(teacher_id):
    """重置教师密码"""
    teacher = Teacher.query.get_or_404(teacher_id)

    # 重置为工号后6位
    new_password = teacher.teacher_id[-6:] if len(teacher.teacher_id) >= 6 else teacher.teacher_id
    teacher.set_password(new_password)

    db.session.commit()

    flash(f'教师 "{teacher.username}" 密码已重置为: {new_password}', 'success')
    return redirect(url_for('admin.teacher_list'))


@bp.route('/teachers/<int:teacher_id>/delete', methods=['POST'])
@login_required
@admin_required
def teacher_delete(teacher_id):
    """删除教师"""
    teacher = Teacher.query.get_or_404(teacher_id)

    # 检查是否有课程关联
    if teacher.courses:  # 直接检查列表是否为空
        flash('无法删除该教师，因为已有课程关联', 'error')
        return redirect(url_for('admin.teacher_list'))

    # 检查是否有其他关联（比如成绩记录等）
    # 根据您的业务逻辑添加其他检查

    # 删除教师
    db.session.delete(teacher)
    db.session.commit()

    flash(f'教师 "{teacher.username}" 已删除', 'success')
    return redirect(url_for('admin.teacher_list'))


@bp.route('/teachers/<int:teacher_id>/courses', methods=['GET', 'POST'])
@login_required
@admin_required
def teacher_courses(teacher_id):
    """管理教师课程绑定"""
    teacher = Teacher.query.get_or_404(teacher_id)
    form = TeacherCourseForm()

    # 设置表单的初始值
    if request.method == 'GET':
        form.course_ids.data = [course.id for course in teacher.courses]

    if form.validate_on_submit():
        try:
            # 清除现有的课程绑定
            teacher.courses.clear()

            # 添加新的课程绑定
            selected_courses = Course.query.filter(Course.id.in_(form.course_ids.data)).all()
            teacher.courses.extend(selected_courses)

            db.session.commit()
            flash(f'教师 "{teacher.username}" 的课程绑定已更新', 'success')
            return redirect(url_for('admin.teacher_edit', teacher_id=teacher_id))

        except Exception as e:
            db.session.rollback()
            flash('课程绑定更新失败', 'error')

    return render_template('admin/teachers/courses.html',
                           form=form,
                           teacher=teacher)


# ==================== 学生管理 ====================

@bp.route('/students')
@login_required
@admin_required
def student_list():
    """学生列表"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    class_filter = request.args.get('class_id', type=int)

    query = Student.query

    if class_filter:
        query = query.filter(Student.class_id == class_filter)

    students = query.order_by(Student.student_id).paginate(
        page=page, per_page=per_page, error_out=False
    )

    classes = Class.query.order_by(Class.class_name).all()

    return render_template('admin/students/list.html',
                           students=students,
                           classes=classes,
                           current_class=class_filter)


@bp.route('/students/create', methods=['GET', 'POST'])
@login_required
@admin_required
def student_create():
    """创建学生账户"""
    form = StudentForm()

    if form.validate_on_submit():
        # 检查用户名和学生学号是否已存在
        if User.query.filter_by(username=form.username.data).first():
            flash('用户名已存在', 'error')
            return render_template('admin/students/create.html', form=form)

        if Student.query.filter_by(student_id=form.student_id.data).first():
            flash('学号已存在', 'error')
            return render_template('admin/students/create.html', form=form)

        # 创建学生用户
        student = Student(
            username=form.username.data,
            student_id=form.student_id.data,
            email=form.email.data,
            phone=form.phone.data,
            class_id=form.class_id.data,
            major=form.major.data,
            role=RoleType.STUDENT
        )

        # 设置初始密码（学号后6位）
        initial_password = form.student_id.data[-6:] if len(form.student_id.data) >= 6 else form.student_id.data
        student.set_password(initial_password)

        db.session.add(student)
        db.session.commit()

        flash(f'学生 "{form.username.data}" 创建成功，初始密码为: {initial_password}', 'success')
        return redirect(url_for('admin.student_list'))

    return render_template('admin/students/create.html', form=form)


@bp.route('/students/<int:student_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def student_edit(student_id):
    """编辑学生信息"""
    student = Student.query.get_or_404(student_id)
    form = StudentForm(obj=student)

    if form.validate_on_submit():
        # 检查用户名是否与其他用户冲突
        existing_user = User.query.filter(
            User.username == form.username.data,
            User.id != student_id
        ).first()

        if existing_user:
            flash('用户名已存在', 'error')
            return render_template('admin/students/edit.html', form=form, student=student)

        # 检查学号是否与其他学生冲突
        existing_student = Student.query.filter(
            Student.student_id == form.student_id.data,
            Student.id != student_id
        ).first()

        if existing_student:
            flash('学号已存在', 'error')
            return render_template('admin/students/edit.html', form=form, student=student)

        student.username = form.username.data
        student.student_id = form.student_id.data
        student.email = form.email.data
        student.phone = form.phone.data
        student.class_id = form.class_id.data
        student.major = form.major.data

        db.session.commit()
        flash(f'学生 "{form.username.data}" 更新成功', 'success')
        return redirect(url_for('admin.student_list'))

    return render_template('admin/students/edit.html', form=form, student=student)


@bp.route('/students/<int:student_id>/reset-password', methods=['POST'])
@login_required
@admin_required
def student_reset_password(student_id):
    """重置学生密码"""
    student = Student.query.get_or_404(student_id)

    # 重置为学号后6位
    new_password = student.student_id[-6:] if len(student.student_id) >= 6 else student.student_id
    student.set_password(new_password)

    db.session.commit()

    flash(f'学生 "{student.username}" 密码已重置为: {new_password}', 'success')
    return redirect(url_for('admin.student_list'))
