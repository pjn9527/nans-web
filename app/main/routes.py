from flask import jsonify, request, current_app
from app.main import bp
from app.models import Project, DevLog, Reaction, db
import sqlalchemy as sa
from hashlib import md5

@bp.route('/')
@bp.route('/index')
def index():
    # 这里不需要传 projects 数据，因为你的 index.html 是用 Vue 异步加载 /api/projects 的
    # 所以直接渲染模板就行，非常干净
    return render_template('index.html')

# 辅助函数：生成访客指纹 (IP + UserAgent)
def get_visitor_hash():
    ip = request.remote_addr
    ua = request.headers.get('User-Agent', '')
    raw = f"{ip}|{ua}"
    return md5(raw.encode('utf-8')).hexdigest()

@bp.route('/api/projects', methods=['GET'])
def get_projects():
    # 1. 查询所有已发布的项目
    query = sa.select(Project).order_by(Project.timestamp.desc())
    projects = db.session.scalars(query).all()
    
    # 2. 转换
    data = [p.to_dict() for p in projects]
    return jsonify(data)

@bp.route('/api/projects/<int:id>', methods=['GET'])
def get_project_detail(id):
    project = db.session.get(Project, id)
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    # 【改动】统计浏览量 (简单的 +1 逻辑)
    # 注意：更严谨的做法是像 Reaction 那样防刷，但浏览量通常可以宽容一些
    project.views += 1
    db.session.commit()

    # 【改动】获取该项目的 DevLog，按时间倒序
    logs = db.session.scalars(
        sa.select(DevLog).where(DevLog.project_id == id).order_by(DevLog.timestamp.desc())
    ).all()

    data = project.to_dict()
    # 这里 key 建议改为 logs，与前端保持语义一致
    data['logs'] = [log.to_dict() for log in logs]
    
    return jsonify(data)

# 【改动】新的互动接口
# 以前是 /api/updates/... 现在语义上改为 /api/logs/...
@bp.route('/api/logs/<int:id>/react', methods=['POST'])
def react_log(id):
    dev_log = db.session.get(DevLog, id)
    if not dev_log:
        return jsonify({'error': 'DevLog not found'}), 404
    
    data = request.get_json()
    emoji_type = data.get('type') # 'fire', 'heart', 'rocket'

    if emoji_type not in ['fire', 'heart', 'rocket']:
        return jsonify({'error': 'Invalid emoji type'}), 400

    visitor_hash = get_visitor_hash()

    # 【核心逻辑】尝试添加一条 Reaction 记录
    # 也就是： "这个访客" 对 "这条日志" 点了 "这个表情"
    existing_reaction = db.session.scalar(
        sa.select(Reaction).where(
            Reaction.visitor_hash == visitor_hash,
            Reaction.dev_log_id == id,
            Reaction.emoji_type == emoji_type
        )
    )

    if existing_reaction:
        # 如果已经点过了，这里可以根据需求决定：
        # 1. 什么都不做 (幂等)
        # 2. 取消点赞 (Toggle)
        # 这里我们暂时由你决定，目前策略是：什么都不做，直接返回成功
        pass 
    else:
        # 没点过，新增一条
        new_reaction = Reaction(
            emoji_type=emoji_type, 
            visitor_hash=visitor_hash, 
            dev_log=dev_log
        )
        db.session.add(new_reaction)
        db.session.commit()
    
    # 返回最新的日志数据（包含重新计算后的计数）
    return jsonify(dev_log.to_dict())


from flask import render_template

@bp.route('/project/<slug>')
def project_detail(slug):
    # 1. 根据 slug 查找项目
    query = sa.select(Project).where(Project.slug == slug)
    project = db.session.scalar(query)
    
    # 2. 如果找不到，返回 404 错误页
    if not project:
        return render_template('errors/404.html'), 404

    # 3. 浏览量 +1
    project.views += 1
    db.session.commit()
    
    # 4. 获取该项目的日志 (按时间倒序)
    logs = db.session.scalars(
        sa.select(DevLog).where(DevLog.project_id == project.id).order_by(DevLog.timestamp.desc())
    ).all()
    
    # 5. 渲染模板
    return render_template('project_detail.html', project=project, logs=logs)