from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_migrate import Migrate

db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()

def create_app(config_name='default'):
    print("📡 正在创建Flask应用...")
    app = Flask(__name__)
    
    # 加载配置
    print("📡 正在加载配置...")
    from app.config import config
    app.config.from_object(config[config_name])
    
    # 设置 JSON 响应不转义中文
    app.config['JSON_AS_ASCII'] = False

    # 初始化上传目录
    print("📡 正在初始化上传目录...")
    config[config_name].init_app(app)
    
    # 初始化扩展
    print("📡 正在初始化扩展...")
    db.init_app(app)
    jwt.init_app(app)
    CORS(app)
    migrate.init_app(app, db)
    
    # 注册蓝图
    print("📡 正在注册蓝图...")
    from app.routes import users
    app.register_blueprint(users.bp, url_prefix='/api/v1/users')
    print(f"  ✅ 已注册用户蓝图: /api/v1/users")
    
    from app.routes import students
    app.register_blueprint(students.bp, url_prefix='/api/v1/students')
    print(f"  ✅ 已注册学生蓝图: /api/v1/students")
    
    from app.routes import courses
    app.register_blueprint(courses.bp, url_prefix='/api/v1/courses')
    print(f"  ✅ 已注册课程蓝图: /api/v1/courses")
    
    print("📡 应用创建完成")
    return app
