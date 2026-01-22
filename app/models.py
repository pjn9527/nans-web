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


# === 2. 项目/作品模型 (已升级并添加新功能) ===
class Project(db.Model):
    __tablename__ = 'project'
    
    # 基础字段 (已统一为 so.Mapped 风格)
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

    # 【新增功能 1】进度条 (0-100)
    progress: so.Mapped[int] = so.mapped_column(sa.Integer, default=0)

    # 【新增功能 2】关联推文更新 (一对多关系)
    # cascade='all, delete-orphan' 意思是：如果删除了项目，它的推文也会自动被删除
    updates: so.Mapped[List['ProjectUpdate']] = so.relationship(back_populates='project', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'slug': self.slug,
            'description': self.description,
            'image_url': self.image_url,
            'demo_link': self.demo_link,
            'source_link': self.source_link,
            'progress': self.progress, # 返回进度数据
            'timestamp': self.timestamp.isoformat() + 'Z' if self.timestamp else None
        }

    def __repr__(self):
        return '<Project {}>'.format(self.title)


# === 3. 【新表】项目推文/更新日志 ===
class ProjectUpdate(db.Model):
    __tablename__ = 'project_update'

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    content: so.Mapped[str] = so.mapped_column(sa.Text) # 推文内容
    timestamp: so.Mapped[datetime] = so.mapped_column(index=True, default=lambda: datetime.now(timezone.utc))
    
    # 外键：关联到 Project 表的 id
    project_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('project.id'))
    project: so.Mapped['Project'] = so.relationship(back_populates='updates')

    # 【新增功能 3】Emoji 计数器
    count_fire: so.Mapped[int] = so.mapped_column(sa.Integer, default=0)   # 🔥
    count_heart: so.Mapped[int] = so.mapped_column(sa.Integer, default=0)  # ❤️
    count_rocket: so.Mapped[int] = so.mapped_column(sa.Integer, default=0) # 🚀

    def to_dict(self):
        return {
            'id': self.id,
            'content': self.content,
            'timestamp': self.timestamp.isoformat() + 'Z',
            'reactions': {
                'fire': self.count_fire,
                'heart': self.count_heart,
                'rocket': self.count_rocket
            }
        }