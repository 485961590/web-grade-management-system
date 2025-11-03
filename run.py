# run.py
from app import create_app
from app.models import db

# 创建应用实例
app = create_app()


# 测试数据库连接和表状态
def test_database():
    try:
        with app.app_context():
            db.session.execute(db.text('SELECT 1'))
            print("数据库连接成功！")
            return True
    except Exception as e:
        print(f"数据库测试失败: {e}")
        return False


if __name__ == '__main__':
    # 测试数据库连接
    test_database()

    # 启动Flask开发服务器
    print("启动Flask开发服务器...")
    print("访问 http://127.0.0.1:5000 查看系统")

    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )
