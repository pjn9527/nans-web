from flask import render_template, flash, redirect, url_for, request
from urllib.parse import urlsplit
from flask_login import current_user, login_user, logout_user
import sqlalchemy as sa
from app import db
from app.auth import bp
from app.auth.forms import LoginForm
from app.models import User

@bp.route('/login', methods=['GET', 'POST'])
def login():
    # 1. 如果已经登录了，直接去后台
    if current_user.is_authenticated:
        return redirect(url_for('admin.index'))

    form = LoginForm()
    if form.validate_on_submit():
        # 2. 去数据库找这个人
        user = db.session.scalar(
            db.select(User).where(User.username == form.username.data))
        
        # 3. 验证密码
        if user is None or not user.check_password(form.password.data):
            flash('用户名或密码错误')
            return redirect(url_for('auth.login'))
        
        # 4. 登进去！
        login_user(user, remember=form.remember_me.data)
        
        # 5. 处理跳转 (如果是被踢出来的，登录后跳回原处)
        next_page = request.args.get('next')
        if not next_page or urlsplit(next_page).netloc != '':
            next_page = url_for('admin.index')
        return redirect(next_page)

    return render_template('auth/login.html', title='登录', form=form)

@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))