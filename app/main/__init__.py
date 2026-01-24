from flask import Blueprint

# 1. 创建蓝图对象
bp = Blueprint('main', __name__)

# 2. 导入路由 (必须放在最后，防止循环引用)
from app.main import routes