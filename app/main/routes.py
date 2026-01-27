# [修改 1] 头部导入部分：新增 requests, Response, stream_with_context
from flask import jsonify, request, current_app, render_template, Response, stream_with_context
from app.main import bp
from app.models import Project, DevLog, Reaction, db
import sqlalchemy as sa
from hashlib import md5
import requests  # <--- 必须导入这个库

@bp.route('/')
@bp.route('/index')
def index():
    return render_template('index.html')

# 辅助函数：生成访客指纹
def get_visitor_hash():
    ip = request.remote_addr
    ua = request.headers.get('User-Agent', '')
    raw = f"{ip}|{ua}"
    return md5(raw.encode('utf-8')).hexdigest()

@bp.route('/api/projects', methods=['GET'])
def get_projects():
    query = sa.select(Project).order_by(Project.timestamp.desc())
    projects = db.session.scalars(query).all()
    data = [p.to_dict() for p in projects]
    return jsonify(data)

@bp.route('/api/projects/<int:id>', methods=['GET'])
def get_project_detail(id):
    project = db.session.get(Project, id)
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    project.views += 1
    db.session.commit()

    logs = db.session.scalars(
        sa.select(DevLog).where(DevLog.project_id == id).order_by(DevLog.timestamp.desc())
    ).all()

    data = project.to_dict()
    data['logs'] = [log.to_dict() for log in logs]
    return jsonify(data)

@bp.route('/api/logs/<int:id>/react', methods=['POST'])
def react_log(id):
    dev_log = db.session.get(DevLog, id)
    if not dev_log:
        return jsonify({'error': 'DevLog not found'}), 404
    
    data = request.get_json()
    emoji_type = data.get('type')

    if emoji_type not in ['fire', 'heart', 'rocket']:
        return jsonify({'error': 'Invalid emoji type'}), 400

    visitor_hash = get_visitor_hash()

    existing_reaction = db.session.scalar(
        sa.select(Reaction).where(
            Reaction.visitor_hash == visitor_hash,
            Reaction.dev_log_id == id,
            Reaction.emoji_type == emoji_type
        )
    )

    if existing_reaction:
        pass 
    else:
        new_reaction = Reaction(
            emoji_type=emoji_type, 
            visitor_hash=visitor_hash, 
            dev_log=dev_log
        )
        db.session.add(new_reaction)
        db.session.commit()
    
    return jsonify(dev_log.to_dict())

@bp.route('/project/<slug>')
def project_detail(slug):
    query = sa.select(Project).where(Project.slug == slug)
    project = db.session.scalar(query)
    
    # 【核心修改点】
    if not project:
        # 原代码：return render_template('errors/404.html'), 404
        # 修改为：返回 JSON，彻底避免 500 报错
        return jsonify({
            'error': 'Project not found', 
            'message': f'The project "{slug}" does not exist or has been removed.'
        }), 404

    # 浏览量 +1
    project.views += 1
    db.session.commit()
    
    # 获取开发日志
    logs = db.session.scalars(
        sa.select(DevLog).where(DevLog.project_id == project.id).order_by(DevLog.timestamp.desc())
    ).all()
    
    # 正常情况依然渲染详情页模板
    return render_template('project_detail.html', project=project, logs=logs)

# [修改 2] 底部新增：Bing 图片代理路由
# 这就是解决内地访问背景图白屏的关键代码
@bp.route('/proxy/bing-bg')
def bing_background():
    # 目标：Bing 每日一图接口
    target_url = "https://bing.biturl.top/?resolution=1920&format=image&index=0&mkt=zh-CN"
    headers = {
        # 伪装成浏览器，防止被 Bing 拦截
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        # stream=True 确保数据流式传输，不占用服务器内存
        req = requests.get(target_url, headers=headers, stream=True, timeout=5)
        # 透传 Content-Type (image/jpeg)
        return Response(stream_with_context(req.iter_content(chunk_size=1024)), 
                        content_type=req.headers.get('content-type', 'image/jpeg'))
    except Exception as e:
        # 如果出错了，返回 404，前端虽然拿不到图但不会崩
        current_app.logger.error(f"Bing Proxy Error: {e}")
        return "", 404