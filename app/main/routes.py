from flask import jsonify, request
from app.main import bp
from app.models import Project, db, ProjectUpdate
import sqlalchemy as sa

@bp.route('/api/projects', methods=['GET'])
def get_projects():
    # 1. 从数据库查询所有项目
    query = sa.select(Project).order_by(Project.timestamp.desc())
    projects = db.session.scalars(query).all()
    
    # 2. 把数据库对象转换成字典 (JSON)
    data = [p.to_dict() for p in projects]
    
    # 3. 返回 JSON 数据
    return jsonify(data)


# 获取单个项目详情 + 推文列表
@bp.route('/api/projects/<int:id>', methods=['GET'])
def get_project_detail(id):
    project = db.session.get(Project, id)
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    # 获取该项目的所有推文，按时间倒序
    updates = db.session.scalars(
        sa.select(ProjectUpdate).where(ProjectUpdate.project_id == id).order_by(ProjectUpdate.timestamp.desc())
    ).all()

    data = project.to_dict()
    data['updates'] = [u.to_dict() for u in updates]
    
    return jsonify(data)

# Emoji 点赞接口
@bp.route('/api/updates/<int:id>/react', methods=['POST'])
def react_update(id):
    update = db.session.get(ProjectUpdate, id)
    if not update:
        return jsonify({'error': 'Update not found'}), 404
    
    data = request.get_json()
    emoji_type = data.get('type') # 'fire', 'heart', 'rocket'

    if emoji_type == 'fire':
        update.count_fire += 1
    elif emoji_type == 'heart':
        update.count_heart += 1
    elif emoji_type == 'rocket':
        update.count_rocket += 1
    
    db.session.commit()
    return jsonify(update.to_dict()) # 返回最新的计数