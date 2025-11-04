from flask import render_template, redirect, url_for, flash, request, Blueprint
from flask_login import login_required, current_user
from sqlalchemy import or_

from app.models import db, Course, Teacher, Student, Class, User, RoleType, Grade
from app.admin.forms import CourseForm, TeacherForm, StudentForm, TeacherCourseForm, ClassForm, GradeForm
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
    search = request.args.get('search', '')
    major_filter = request.args.get('major', '')

    query = Student.query

    # 班级筛选
    if class_filter:
        query = query.filter(Student.class_id == class_filter)

    # 搜索功能
    if search:
        query = query.filter(
            db.or_(
                Student.student_id.ilike(f'%{search}%'),
                Student.username.ilike(f'%{search}%'),
                Student.major.ilike(f'%{search}%')
            )
        )

    # 专业筛选
    if major_filter:
        query = query.filter(Student.major == major_filter)

    students = query.order_by(Student.student_id).paginate(
        page=page, per_page=per_page, error_out=False
    )

    classes = Class.query.order_by(Class.class_name).all()

    # 获取所有专业用于筛选
    majors = db.session.query(Student.major).distinct().all()
    majors = [major[0] for major in majors if major[0]]

    return render_template('admin/students/list.html',
                           students=students,
                           classes=classes,
                           majors=majors,
                           current_class=class_filter,
                           current_major=major_filter)


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


@bp.route('/students/<int:student_id>/delete', methods=['POST'])
@login_required
@admin_required
def student_delete(student_id):
    """删除学生"""
    student = Student.query.get_or_404(student_id)

    # 检查是否有成绩关联
    if student.grades.count() > 0:
        flash('无法删除该学生，因为已有成绩记录关联', 'error')
        return redirect(url_for('admin.student_list'))

    # 删除学生
    db.session.delete(student)
    db.session.commit()

    flash(f'学生 "{student.username}" 已删除', 'success')
    return redirect(url_for('admin.student_list'))


# ==================== 班级管理 ====================

@bp.route('/classes')
@login_required
@admin_required
def class_list():
    """班级列表"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    search = request.args.get('search', '')
    major_filter = request.args.get('major', '')

    query = Class.query

    # 搜索功能
    if search:
        query = query.filter(
            db.or_(
                Class.class_code.ilike(f'%{search}%'),
                Class.class_name.ilike(f'%{search}%'),
                Class.major.ilike(f'%{search}%')
            )
        )

    # 专业筛选
    if major_filter:
        query = query.filter(Class.major == major_filter)

    classes = query.order_by(Class.class_code).paginate(
        page=page, per_page=per_page, error_out=False
    )

    # 获取所有专业用于筛选
    majors = db.session.query(Class.major).distinct().all()
    majors = [major[0] for major in majors if major[0]]

    return render_template('admin/classes/list.html',
                           classes=classes,
                           majors=majors,
                           current_major=major_filter)


@bp.route('/classes/create', methods=['GET', 'POST'])
@login_required
@admin_required
def class_create():
    """创建班级"""
    form = ClassForm()

    if form.validate_on_submit():
        # 检查班级代码是否已存在
        existing_class = Class.query.filter_by(class_code=form.class_code.data).first()
        if existing_class:
            flash('班级代码已存在', 'error')
            return render_template('admin/classes/create.html', form=form)

        class_ = Class(
            class_code=form.class_code.data,
            class_name=form.class_name.data,
            major=form.major.data,
            class_teacher_id=form.class_teacher_id.data if form.class_teacher_id.data != 0 else None
        )

        db.session.add(class_)
        db.session.commit()

        flash(f'班级 "{form.class_name.data}" 创建成功', 'success')
        return redirect(url_for('admin.class_list'))

    return render_template('admin/classes/create.html', form=form)


@bp.route('/classes/<int:class_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def class_edit(class_id):
    """编辑班级"""
    class_ = Class.query.get_or_404(class_id)
    form = ClassForm(obj=class_)

    if form.validate_on_submit():
        # 检查班级代码是否与其他班级冲突
        existing_class = Class.query.filter(
            Class.class_code == form.class_code.data,
            Class.id != class_id
        ).first()

        if existing_class:
            flash('班级代码已存在', 'error')
            return render_template('admin/classes/edit.html', form=form, class_=class_)

        class_.class_code = form.class_code.data
        class_.class_name = form.class_name.data
        class_.major = form.major.data
        class_.class_teacher_id = form.class_teacher_id.data if form.class_teacher_id.data != 0 else None

        db.session.commit()
        flash(f'班级 "{form.class_name.data}" 更新成功', 'success')
        return redirect(url_for('admin.class_list'))

    return render_template('admin/classes/edit.html', form=form, class_=class_)


@bp.route('/classes/<int:class_id>/delete', methods=['POST'])
@login_required
@admin_required
def class_delete(class_id):
    """删除班级"""
    class_ = Class.query.get_or_404(class_id)

    # 检查是否有学生关联
    if class_.students.count() > 0:
        flash('无法删除该班级，因为已有学生关联', 'error')
        return redirect(url_for('admin.class_list'))

    db.session.delete(class_)
    db.session.commit()

    flash(f'班级 "{class_.class_name}" 已删除', 'success')
    return redirect(url_for('admin.class_list'))


# ==================== 成绩管理 ====================

@bp.route('/grades')
@login_required
@admin_required
def grade_list():
    """成绩列表"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    student_search = request.args.get('student_search', '')
    course_search = request.args.get('course_search', '')
    semester_filter = request.args.get('semester_filter', '')
    teacher_filter = request.args.get('teacher_filter', type=int)

    query = Grade.query

    # 学生搜索
    if student_search:
        query = query.join(Student).filter(
            db.or_(
                Student.username.ilike(f'%{student_search}%'),
                Student.student_id.ilike(f'%{student_search}%')
            )
        )

    # 课程搜索
    if course_search:
        query = query.join(Course).filter(
            db.or_(
                Course.course_name.ilike(f'%{course_search}%'),
                Course.course_code.ilike(f'%{course_search}%')
            )
        )

    # 学期筛选
    if semester_filter:
        query = query.filter(Grade.semester == semester_filter)

    # 教师筛选
    if teacher_filter:
        query = query.filter(Grade.teacher_id == teacher_filter)

    grades = query.order_by(Grade.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    # 获取教师列表用于筛选
    teachers = Teacher.query.order_by(Teacher.username).all()

    return render_template('admin/grades/list.html',
                           grades=grades,
                           teachers=teachers,
                           student_search=student_search,
                           course_search=course_search,
                           semester_filter=semester_filter,
                           teacher_filter=teacher_filter)


@bp.route('/grades/create', methods=['GET', 'POST'])
@login_required
@admin_required
def grade_create():
    """录入成绩"""
    form = GradeForm()

    # 检查是否有教师数据
    teacher_count = Teacher.query.count()
    if teacher_count == 0:
        flash('请先创建教师账户才能录入成绩', 'error')
        return redirect(url_for('admin.teacher_create'))

    if form.validate_on_submit():
        # 检查是否已存在相同学生、课程、学期的成绩记录
        existing_grade = Grade.query.filter_by(
            student_id=form.student_id.data,
            course_id=form.course_id.data,
            semester=form.semester.data,
            is_makeup=form.is_makeup.data
        ).first()

        if existing_grade:
            flash('该学生在此课程和学期下已有成绩记录', 'error')
            return render_template('admin/grades/create.html', form=form)

        grade = Grade(
            student_id=form.student_id.data,
            course_id=form.course_id.data,
            teacher_id=form.teacher_id.data,
            score=form.score.data,
            semester=form.semester.data,
            academic_year=form.academic_year.data,
            is_makeup=form.is_makeup.data
        )

        db.session.add(grade)
        db.session.commit()

        flash('成绩录入成功', 'success')
        return redirect(url_for('admin.grade_list'))

    return render_template('admin/grades/create.html', form=form)


@bp.route('/grades/<int:grade_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def grade_edit(grade_id):
    """编辑成绩"""
    grade = Grade.query.get_or_404(grade_id)
    form = GradeForm(obj=grade)

    if form.validate_on_submit():
        # 检查是否与其他成绩记录冲突（排除当前记录）
        existing_grade = Grade.query.filter(
            Grade.student_id == form.student_id.data,
            Grade.course_id == form.course_id.data,
            Grade.semester == form.semester.data,
            Grade.is_makeup == form.is_makeup.data,
            Grade.id != grade_id
        ).first()

        if existing_grade:
            flash('该学生在此课程和学期下已有其他成绩记录', 'error')
            return render_template('admin/grades/edit.html', form=form, grade=grade)

        # 记录修改前的成绩
        previous_score = grade.score

        grade.student_id = form.student_id.data
        grade.course_id = form.course_id.data
        grade.score = form.score.data
        grade.semester = form.semester.data
        grade.academic_year = form.academic_year.data
        grade.is_makeup = form.is_makeup.data

        # 创建成绩修改日志
        if previous_score != form.score.data:
            modification_log = GradeModificationLog(
                grade_id=grade.id,
                previous_score=previous_score,
                new_score=form.score.data,
                modified_by=current_user.id,
                reason=f"管理员 {current_user.username} 修改成绩"
            )
            db.session.add(modification_log)

        db.session.commit()
        flash('成绩更新成功', 'success')
        return redirect(url_for('admin.grade_list'))

    return render_template('admin/grades/edit.html', form=form, grade=grade)


@bp.route('/grades/<int:grade_id>/delete', methods=['POST'])
@login_required
@admin_required
def grade_delete(grade_id):
    """删除成绩"""
    grade = Grade.query.get_or_404(grade_id)

    # 删除相关的修改日志
    GradeModificationLog.query.filter_by(grade_id=grade_id).delete()

    db.session.delete(grade)
    db.session.commit()

    flash('成绩记录已删除', 'success')
    return redirect(url_for('admin.grade_list'))


@bp.route('/grades/<int:grade_id>/lock', methods=['POST'])
@login_required
@admin_required
def grade_lock(grade_id):
    """锁定成绩（防止修改）"""
    grade = Grade.query.get_or_404(grade_id)
    grade.is_locked = True
    db.session.commit()
    flash('成绩已锁定', 'success')
    return redirect(url_for('admin.grade_list'))


@bp.route('/grades/<int:grade_id>/unlock', methods=['POST'])
@login_required
@admin_required
def grade_unlock(grade_id):
    """解锁成绩"""
    grade = Grade.query.get_or_404(grade_id)
    grade.is_locked = False
    db.session.commit()
    flash('成绩已解锁', 'success')
    return redirect(url_for('admin.grade_list'))


@bp.route('/grades/import', methods=['GET', 'POST'])
@login_required
@admin_required
def grade_import():
    """批量导入成绩"""
    if request.method == 'POST':
        # 这里可以实现Excel或CSV文件导入功能
        flash('批量导入功能开发中', 'info')
        return redirect(url_for('admin.grade_list'))

    return render_template('admin/grades/import.html')


@bp.route('/grades/statistics')
@login_required
@admin_required
def grade_statistics():
    """成绩统计"""
    # 基础统计
    total_grades = Grade.query.count()
    avg_score = db.session.query(db.func.avg(Grade.score)).scalar() or 0
    max_score = db.session.query(db.func.max(Grade.score)).scalar() or 0
    min_score = db.session.query(db.func.min(Grade.score)).scalar() or 0

    # 成绩分布统计
    score_distribution = {
        '优秀(90-100)': Grade.query.filter(Grade.score.between(90, 100)).count(),
        '良好(80-89)': Grade.query.filter(Grade.score.between(80, 89)).count(),
        '中等(70-79)': Grade.query.filter(Grade.score.between(70, 79)).count(),
        '及格(60-69)': Grade.query.filter(Grade.score.between(60, 69)).count(),
        '不及格(0-59)': Grade.query.filter(Grade.score.between(0, 59)).count()
    }

    # 各课程平均分
    course_stats = db.session.query(
        Course.course_name,
        db.func.avg(Grade.score).label('avg_score'),
        db.func.count(Grade.id).label('count')
    ).join(Grade.course).group_by(Course.id).all()

    stats = {
        'total_grades': total_grades,
        'avg_score': round(avg_score, 2),
        'max_score': max_score,
        'min_score': min_score,
        'score_distribution': score_distribution,
        'course_stats': course_stats
    }

    return render_template('admin/grades/statistics.html', stats=stats)
