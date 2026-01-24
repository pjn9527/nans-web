from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

# 初始化 Flask 应用
app = Flask(__name__)
app.config.from_object(Config)

# 初始化数据库和迁移工具
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# === 初始化登录管理 (这是我们今天新加的) ===
login = LoginManager(app)
# 注意：这里改成了 'auth.login'
# 因为你的登录路由 login 在 app/auth/routes.py 里，所以它属于 auth 蓝图
login.login_view = 'auth.login' 

# === 注册蓝图 (关键！让 Flask 知道这三个文件夹的存在) ===

# 1. 错误处理蓝图
from app.errors import bp as errors_bp
app.register_blueprint(errors_bp)

# 2. 认证蓝图 (登录/注册)
# url_prefix='/auth' 意味着所有路由前面都会加 /auth
# 比如 /login 变成 /auth/login
from app.auth import bp as auth_bp
app.register_blueprint(auth_bp, url_prefix='/auth')

# 3. 主功能蓝图 (首页等)
from app.main import bp as main_bp
app.register_blueprint(main_bp)

# === 导入模型 (防止数据库迁移找不到表) ===
from app import models