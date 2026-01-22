from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired

# 注意：我们删除了 from flask_babel import ... 这一行

class LoginForm(FlaskForm):
    # 把 _l('Username') 这种写法直接改成 'Username'
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')