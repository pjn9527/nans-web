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
    # 1. 如果已经登录，不要去 main.index (那是API)，直接去后台 admin.index
    if current_user.is_authenticated:
        return redirect(url_for('admin.index'))
        
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.scalar(sa.select(User).where(User.username == form.username.data))
        
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('auth.login'))
            
        login_user(user, remember=form.remember_me.data)
        
        next_page = request.args.get('next')
        if not next_page or urlsplit(next_page).netloc != '':
            # 2. 登录成功后的默认跳转，也改成后台 admin.index
            next_page = url_for('admin.index')
        return redirect(next_page)
    
    return render_template('auth/login.html', title='Sign In', form=form)

@bp.route('/logout')
def logout():
    logout_user()
    # 3. 登出后，不要去首页(那是Vue的地盘)，直接跳回登录页，方便下次登录
    return redirect(url_for('auth.login'))