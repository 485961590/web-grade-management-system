from flask import render_template, redirect, url_for, flash, request, Blueprint
from flask_login import login_required, current_user
from sqlalchemy import desc

from app.models import Grade, Course
from app.student.decorators import student_required

bp = Blueprint('student', __name__, url_prefix='/student')


@bp.route('/grades')
@login_required
@student_required
def grades():
    """查看我的成绩 - 学生唯一功能"""
    page = request.args.get('page', 1, type=int)
    per_page = 15

    # 搜索过滤
    course_search = request.args.get('course_search', '')
    semester_filter = request.args.get('semester_filter', '')

    # 基础查询 - 只显示当前学生的成绩
    query = Grade.query.filter_by(student_id=current_user.id)

    # 课程搜索
    if course_search:
        query = query.join(Course).filter(
            Course.course_name.ilike(f'%{course_search}%') |
            Course.course_code.ilike(f'%{course_search}%')
        )

    # 学期筛选
    if semester_filter:
        query = query.filter_by(semester=semester_filter)

    # 按时间倒序排列
    grades = query.order_by(desc(Grade.created_at)).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return render_template('student/grades.html',
                           grades=grades,
                           course_search=course_search,
                           semester_filter=semester_filter)