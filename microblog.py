import sqlalchemy as sa
import sqlalchemy.orm as so
from app import create_app, db
# 只导入现在真正存在的模型
from app.models import User, Project 

app = create_app()

@app.shell_context_processor
def make_shell_context():
    # 更新 shell 上下文，方便你在 flask shell 里调试
    return {'db': db, 'User': User, 'Project': Project}