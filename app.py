# coding:utf-8
from flask import Flask, render_template, session, redirect, url_for, flash
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_wtf import FlaskForm
from flask_sqlalchemy import SQLAlchemy
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Length

from datetime import datetime
import os

basedir = os.path.abspath(os.path.dirname(__file__))  # 获取当前运行文件路径

app = Flask(__name__)
app.config['SECRET_KEY'] = 'hard to guess string'
app.config['SQLALCHEMY_DATABASE_URI'] =\
'sqlite:///' + os.path.join(basedir, 'data.sqlite')
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True  # 该配置为True,则每次请求结束都会自动commit数据库的变动


bootstrap = Bootstrap(app)
moment = Moment(app)
db = SQLAlchemy(app)  # db 对象是 SQLAlchemy 类的实例,表示程序使用的数据库


class NameForm(FlaskForm):
    name = StringField('What is your name?', validators=[DataRequired()])
    password = PasswordField('password',
                             validators=[DataRequired(message=u"密码不能为空"), Length(2, 10, message=u'长度位于2~10之间')],
                             render_kw={'placeholder': u'输入密码'})
    submit = SubmitField('Submit')


class Role(db.Model):
    __tablename__ = 'roles'  # 类变量 __tablename__ 定义在数据库中使用的表名
    id = db.Column(db.Integer, primary_key=True)  # Flask-SQLAlchemy 要求每个模型都要定义主键,这一列经常命名为 id
    name = db.Column(db.String(64),unique=True)
    users = db.relationship

    def __repr__(self):  # 返回一个具有可读性的字符串表示模型,可在调试和测试时使用。
        return '<Role %r>'%self.name  # %r用rper()方法处理对象,%s用str()方法处理对象


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True)

    def __repr__(self):
        return '<User %r>'%self.username

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


# 告诉 Flask 在 URL 映射中把这个视图函数注册为 GET 和 POST 请求的处理程序
# 如果没指定 methods 参数，就只把视图函数注册为 GET 请求的处理程序
@app.route('/', methods=['GET', 'POST'])
def index():
    form = NameForm()
    if form.validate_on_submit():  # 如果数据能被所有验证函数接受，那么该方法的返回值为True
        old_name = session.get('name')
        if old_name is not None and old_name != form.name.data:
            flash('Looks like you have changed your name!')
        session['name'] = form.name.data  # 用户的输入可通过字段的 data 属性获取
        return redirect(url_for('index'))
    return render_template('index.html',
                           form=form,
                           name=session.get('name'),
                           current_time=datetime.utcnow()
                           )
"""
程序可以把数据存储在用户会话中，在请求之间“记住”数据。用户会话是一种私有存
储，存在于每个连接到服务器的客户端中.
默认情况下，用户会话保存在客户端 cookie 中，使用设置的 SECRET_KEY 进
行加密签名。如果篡改了 cookie 中的内容，签名就会失效，会话也会随之失效
"""

if __name__ == '__main__':
	app.run(debug=True)
