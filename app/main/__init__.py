from flask import Blueprint 
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

login = LoginManager(app)         # 👇 新增：初始化登录管理
login.login_view = 'login'        # 👇 新增：告诉它，如果没登录，就踢到 'login' 这个路由去


bp = Blueprint('main', __name__)

from app.main import routes