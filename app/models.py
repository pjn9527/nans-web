from datetime import datetime, timezone
from typing import Optional, List
import sqlalchemy as sa
import sqlalchemy.orm as so
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from hashlib import md5
import re  # <--- [新增] 必须导入 re 模块用于正则替换
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

    # 关联关系
    logs: so.Mapped[List['DevLog']] = so.relationship(back_populates='project', cascade='all, delete-orphan')

    # --- [新增功能开始] 自动生成 Slug ---
    def __init__(self, **kwargs):
        # 这一行确保父类初始化正常执行
        super().__init__(**kwargs)
        # 如果有标题但没 slug，自动生成
        if self.title and not self.slug:
            self.slug = self._generate_slug(self.title)

    @staticmethod
    def _generate_slug(target_str):
        # 1. 转小写
        s = target_str.lower()
        # 2. 移除所有非字母数字字符（保留空格和横杠）
        s = re.sub(r'[^\w\s-]', '', s)
        # 3. 将空格和下划线替换为横杠
        s = re.sub(r'[\s_-]+', '-', s)
        # 4. 去除首尾横杠
        return s.strip('-')
    # --- [新增功能结束] ---

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


# === 3. 开发日志模型 (保持不变) ===
class DevLog(db.Model):
    __tablename__ = 'dev_log'

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    content: so.Mapped[str] = so.mapped_column(sa.Text)
    timestamp: so.Mapped[datetime] = so.mapped_column(index=True, default=lambda: datetime.now(timezone.utc))
    
    project_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('project.id'))
    project: so.Mapped['Project'] = so.relationship(back_populates='logs')

    reactions: so.Mapped[List['Reaction']] = so.relationship(back_populates='dev_log', cascade='all, delete-orphan')
    
    @property
    def reactions_summary(self):
        return {
            'fire': len([r for r in self.reactions if r.emoji_type == 'fire']),
            'heart': len([r for r in self.reactions if r.emoji_type == 'heart']),
            'rocket': len([r for r in self.reactions if r.emoji_type == 'rocket'])
        }
        
    def to_dict(self):
        return {
            'id': self.id,
            'content': self.content,
            'timestamp': self.timestamp.isoformat() + 'Z',
            'reactions_summary': self.reactions_summary
        }

# === 4. 互动/点赞模型 (保持不变) ===
class Reaction(db.Model):
    __tablename__ = 'reaction'
    __table_args__ = (
        sa.UniqueConstraint('visitor_hash', 'dev_log_id', 'emoji_type', name='unique_visitor_reaction'),
    )

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    emoji_type: so.Mapped[str] = so.mapped_column(sa.String(10)) 
    visitor_hash: so.Mapped[str] = so.mapped_column(sa.String(64), index=True)
    timestamp: so.Mapped[datetime] = so.mapped_column(default=lambda: datetime.now(timezone.utc))

    dev_log_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('dev_log.id'))
    dev_log: so.Mapped['DevLog'] = so.relationship(back_populates='reactions')