# create_test_data.py
from app import create_app
from app.models import db, User, Student, Teacher, Admin, RoleType

app = create_app()


def create_test_data():
    with app.app_context():
        # 创建测试用户
        users = [
            # 管理员
            {'username': 'admin', 'password': 'admin123', 'role': RoleType.ADMIN, 'type': 'admin'},
            # 教师
            {'username': 'teacher1', 'password': 'teacher123', 'role': RoleType.TEACHER, 'type': 'teacher'},
            # 学生
            {'username': 'student1', 'password': 'student123', 'role': RoleType.STUDENT, 'type': 'student'},
            # 班主任
            {'username': 'classteacher1', 'password': 'class123', 'role': RoleType.CLASS_TEACHER, 'type': 'teacher'},
        ]

        for user_data in users:
            if user_data['role'] == RoleType.ADMIN:
                user = Admin(username=user_data['username'], role=user_data['role'])
                user.admin_id = user_data['username']
            elif user_data['role'] in [RoleType.TEACHER, RoleType.CLASS_TEACHER]:
                user = Teacher(username=user_data['username'], role=user_data['role'])
                user.teacher_id = user_data['username']
            else:
                user = Student(username=user_data['username'], role=user_data['role'])
                user.student_id = user_data['username']

            user.set_password(user_data['password'])
            db.session.add(user)

        db.session.commit()
        print("✅ 测试数据创建完成！")
        print("测试账号:")
        print("管理员 - admin/admin123")
        print("教师 - teacher1/teacher123")
        print("学生 - student1/student123")
        print("班主任 - classteacher1/class123")


if __name__ == '__main__':
    create_test_data()