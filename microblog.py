import sqlalchemy as sa
import sqlalchemy.orm as so
from app import create_app, db
# 【改动】导入所有新模型
from app.models import User, Project, DevLog, Reaction

app = create_app()

@app.shell_context_processor
def make_shell_context():
    # 【改动】注册到 shell 上下文
    return {
        'db': db, 
        'User': User, 
        'Project': Project, 
        'DevLog': DevLog, 
        'Reaction': Reaction
    }