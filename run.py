from app import create_app
from app.models import db

# 创建Flask应用
app = create_app()


# 测试数据库连接和表状态
def test_database():
    try:
        with app.app_context():
            # 测试连接
            db.session.execute(db.text('SELECT 1'))
            print("✅ 数据库连接成功！")

            # 检查表是否存在
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"📋 现有表格: {tables}")

            return True
    except Exception as e:
        print(f"❌ 数据库测试失败: {e}")
        return False


# 添加一个简单的路由用于测试
@app.route('/')
def hello():
    return '''
    <h1>🎉 Web成绩管理系统已启动！</h1>
    <p><a href="/test-db">测试数据库连接</a></p>
    <p><a href="/create-tables">创建数据库表</a></p>
    '''


@app.route('/test-db')
def test_db_route():
    if test_database():
        return '✅ 数据库连接正常！'
    else:
        return '❌ 数据库连接失败！'


@app.route('/create-tables')
def create_tables_route():
    try:
        with app.app_context():
            db.create_all()
            return '✅ 数据库表创建成功！'
    except Exception as e:
        return f'❌ 创建表失败: {e}'


if __name__ == '__main__':
    # 测试数据库连接
    test_database()

    # 启动Flask开发服务器
    print("🚀 启动Flask开发服务器...")
    print("📍 访问 http://127.0.0.1:5000 查看首页")
    print("📍 访问 http://127.0.0.1:5000/test-db 测试数据库连接")
    print("📍 访问 http://127.0.0.1:5000/create-tables 创建数据库表")

    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )