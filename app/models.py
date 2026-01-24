from datetime import datetime, timezone
from typing import Optional, List
import sqlalchemy as sa
import sqlalchemy.orm as so
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from hashlib import md5
from app import db, login

# === 1. 用户模型 (保持不变) ===
class User(UserMixin, db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(64), index=True, unique=True)
    email: so.Mapped[str] = so.mapped_column(sa.String(120), index=True, unique=True)
    password_hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))
    
    about_me: so.Mapped[Optional[str]] = so.mapped_column(sa.String(140))
    last_seen: so.Mapped[Optional[datetime]] = so.mapped_column(default=lambda: datetime.now(timezone.utc))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return f'https://www.gravatar.com/avatar/{digest}?d=identicon&s={size}'

    def __repr__(self):
        return '<User {}>'.format(self.username)

@login.user_loader
def load_user(id):
    return db.session.get(User, int(id))


# === 2. 项目/作品模型 ===
class Project(db.Model):
    __tablename__ = 'project'
    
    # 基础字段
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    title: so.Mapped[str] = so.mapped_column(sa.String(140))
    slug: so.Mapped[Optional[str]] = so.mapped_column(sa.String(140), unique=True, index=True)
    description: so.Mapped[Optional[str]] = so.mapped_column(sa.Text)
    
    # 链接
    image_url: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))
    demo_link: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))
    source_link: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))
    
    # 状态
    is_published: so.Mapped[bool] = so.mapped_column(default=True)
    timestamp: so.Mapped[datetime] = so.mapped_column(index=True, default=lambda: datetime.now(timezone.utc))
    progress: so.Mapped[int] = so.mapped_column(sa.Integer, default=0)

    # 【Phase 5 新增】统计浏览量
    views: so.Mapped[int] = so.mapped_column(sa.Integer, default=0)

    # 关联关系：改为 'DevLog' (原 ProjectUpdate)
    logs: so.Mapped[List['DevLog']] = so.relationship(back_populates='project', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'slug': self.slug,
            'description': self.description,
            'image_url': self.image_url,
            'links': {
                'demo': self.demo_link,
                'source': self.source_link
            },
            'stats': {
                'progress': self.progress,
                'views': self.views
            },
            'timestamp': self.timestamp.isoformat() + 'Z' if self.timestamp else None
        }

    def __repr__(self):
        return '<Project {}>'.format(self.title)


# === 3. 开发日志模型 (原 ProjectUpdate) ===
# 建议改名为 DevLog，更符合 "碎碎念" 的定义
class DevLog(db.Model):
    __tablename__ = 'dev_log'

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    content: so.Mapped[str] = so.mapped_column(sa.Text) # 支持 Markdown
    timestamp: so.Mapped[datetime] = so.mapped_column(index=True, default=lambda: datetime.now(timezone.utc))
    
    # 外键
    project_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('project.id'))
    project: so.Mapped['Project'] = so.relationship(back_populates='logs')

    # 【重要改动】删除 integer 计数器，改为关联 Reaction 表
    # 这样我们才能追踪 "谁" 点了赞，从而防止无限点击
    reactions: so.Mapped[List['Reaction']] = so.relationship(back_populates='dev_log', cascade='all, delete-orphan')
    @property
    def reactions_summary(self):
        return {
            'fire': len([r for r in self.reactions if r.emoji_type == 'fire']),
            'heart': len([r for r in self.reactions if r.emoji_type == 'heart']),
            'rocket': len([r for r in self.reactions if r.emoji_type == 'rocket'])
        }
    def to_dict(self):
        # 统计逻辑放到 to_dict 里计算，保证数据绝对准确
        return {
            'id': self.id,
            'content': self.content,
            'timestamp': self.timestamp.isoformat() + 'Z',
            'reactions_summary': self.reactions_summary
        }

# === 4. 【Phase 5 新增】互动/点赞记录表 ===
class Reaction(db.Model):
    __tablename__ = 'reaction'
    __table_args__ = (
        # 【核心逻辑】联合唯一索引
        # 确保：同一个 visitor_hash 在同一个 dev_log 下，只能对同一种 emoji 点赞一次
        sa.UniqueConstraint('visitor_hash', 'dev_log_id', 'emoji_type', name='unique_visitor_reaction'),
    )

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    emoji_type: so.Mapped[str] = so.mapped_column(sa.String(10)) # 'fire', 'heart', 'rocket'
    
    # 访客指纹：可以是 IP 的哈希，也可以是前端生成的 uuid 存 cookie
    visitor_hash: so.Mapped[str] = so.mapped_column(sa.String(64), index=True)
    
    timestamp: so.Mapped[datetime] = so.mapped_column(default=lambda: datetime.now(timezone.utc))

    # 外键
    dev_log_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('dev_log.id'))
    dev_log: so.Mapped['DevLog'] = so.relationship(back_populates='reactions')