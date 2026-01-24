import logging
from logging.handlers import SMTPHandler, RotatingFileHandler
import os
from flask import Flask, current_app, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, current_user
from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_cors import CORS
from config import Config

db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_view = 'auth.login'
# login.login_message = _l('Please log in to access this page.')

# === 【关键调整 1】 把安全类的定义移到 Admin 初始化之前 ===
# 否则 Python 执行到 Admin(...) 时，还不知道 SecureAdminIndexView 是什么

class SecureModelView(ModelView):
    def is_accessible(self):
        # 只有登录用户才能看！
        return current_user.is_authenticated

    def inaccessible_callback(self, name, **kwargs):
        # 没登录？踢到登录页去！
        # 注意：这里要用 request.url 获取当前页面，以便登录后跳回来
        return redirect(url_for('auth.login', next=request.url))

class SecureAdminIndexView(AdminIndexView):
    def is_accessible(self):
        return current_user.is_authenticated

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('auth.login', next=request.url))

# === 【关键调整 2】 初始化 Admin 时，挂上首页锁 ===
# 加上 template_mode='bootstrap3' 是为了保证样式兼容性
admin = Admin(name='我的作品集后台', 
              index_view=SecureAdminIndexView())

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # 1. 初始化核心插件
    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    admin.init_app(app)
    CORS(app)

    # 2. 注册 Blueprints
    from app.errors import bp as errors_bp
    app.register_blueprint(errors_bp)

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    # 3. 注册 Admin 视图
    # === 【关键调整 3】 这里必须用 SecureModelView，而不是普通的 ModelView ===
    from app.models import User, Project, ProjectUpdate
    
    existing_views = [v.name for v in admin._views]
    
    if '用户管理' not in existing_views:
        # 👇 这里的 ModelView 全都改成了 SecureModelView
        admin.add_view(SecureModelView(User, db.session, name='用户管理'))
    
    if '作品管理' not in existing_views:
        admin.add_view(SecureModelView(Project, db.session, name='作品管理'))
    
    if 'Project Updates' not in existing_views:
        admin.add_view(SecureModelView(ProjectUpdate, db.session, name='Project Updates'))

    # 4. 日志配置 (保持不变)
    if not app.debug and not app.testing:
        if app.config['MAIL_SERVER']:
            auth = None
            if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
                auth = (app.config['MAIL_USERNAME'],
                        app.config['MAIL_PASSWORD'])
            secure = None
            if app.config['MAIL_USE_TLS']:
                secure = ()
            mail_handler = SMTPHandler(
                mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
                fromaddr='no-reply@' + app.config['MAIL_SERVER'],
                toaddrs=app.config['ADMINS'], subject='Portfolio Failure',
                credentials=auth, secure=secure
            )
            mail_handler.setLevel(logging.ERROR)
            app.logger.addHandler(mail_handler)

        if app.config.get('LOG_TO_STDOUT'):
            stream_handler = logging.StreamHandler()
            stream_handler.setLevel(logging.INFO)
            app.logger.addHandler(stream_handler)
        else:
            if not os.path.exists('logs'):
                os.mkdir('logs')
            file_handler = RotatingFileHandler(
                'logs/microblog.log',
                maxBytes=10240,
                backupCount=10
            )
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s '
                '[in %(pathname)s:%(lineno)d]'
            ))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info('Portfolio startup')

    return app

from app import models