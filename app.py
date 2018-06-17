# coding:utf-8
from flask import Flask, render_template, session, redirect, url_for, flash
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_wtf import FlaskForm
from flask_sqlalchemy import SQLAlchemy
from flask_script import Manager,Shell
from flask_migrate import Migrate, MigrateCommand
from flask_mail import Mail, Message
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Length

from datetime import datetime
from threading import Thread
import os

basedir = os.path.abspath(os.path.dirname(__file__))  # 获取当前运行文件路径

app = Flask(__name__)
app.config['SECRET_KEY'] = 'hard to guess string'
app.config['SQLALCHEMY_DATABASE_URI'] =\
    'sqlite:///' + os.path.join(basedir, 'data.sqlite')
app.config['SQLALCHEMY_COMMIT_TEARDOWN'] = True  # 该配置为True,则每次请求结束都会自动commit数据库的变动
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # 不需要使用TLS


app.config['MAIL_DEBUG'] = True             # 开启debug，便于调试看信息
app.config['MAIL_SUPPRESS_SEND'] = False    # 发送邮件，为True则不发送
app.config['MAIL_SERVER'] = 'smtp.qq.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True  #重要，qq邮箱需要使用SSL
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USERNAME'] = '1241908493@qq.com'
app.config['MAIL_PASSWORD'] = 'ocvcfuajjxdujbdg'


bootstrap = Bootstrap(app)
manager = Manager(app)
moment = Moment(app)
db = SQLAlchemy(app)  # db 对象是 SQLAlchemy 类的实例,表示程序使用的数据库
migrate = Migrate(app, db)
manager.add_command('db', MigrateCommand)
mail = Mail(app)

class NameForm(FlaskForm):
    name = StringField('What is your name?', validators=[DataRequired()])
    password = PasswordField('password',
                             validators=[DataRequired(message=u"密码不能为空"), Length(2, 10, message=u'长度位于2~10之间')],
                             render_kw={'placeholder': u'输入密码'})
    submit = SubmitField('Submit')


class Role(db.Model):
    __tablename__ = 'roles'  # 类变量 __tablename__ 定义在数据库中使用的表名
    id = db.Column(db.Integer, primary_key=True)  # Flask-SQLAlchemy 要求每个模型都要定义主键,这一列经常命名为 id
    name = db.Column(db.String(64), unique=True)
    # backref定义反向关系,这一属性可替代 role_id 访问 Role 模型，此时获取的是模型对象，而不是外键的值
    # lazy = 'dynamic' 参数，禁止自动执行查询
    users = db.relationship('User', backref='role', lazy='dynamic')

    def __repr__(self):  # 返回一个具有可读性的字符串表示模型,可在调试和测试时使用。
        return '<Role %r>' % self.name  # %r用rper()方法处理对象,%s用str()方法处理对象


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)  # index=True为这列创建索引，提升查询效率quit
    # role_id被定义为外键,传给db.ForeignKey()的参数'roles.id'表明,这列的值是roles表中行的id值
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))

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
        user = User.query.filter_by(username=form.name.data).first()
        if user is None:
            user = User(username=form.name.data)
            db.session.add(user)
            session['known'] = False  # 表示换了个user登陆
        else:
            session['known'] = True
        send_email()
        session['name'] = form.name.data  # 用户的输入可通过字段的 data 属性获取
        form.name.data = ''
        return redirect(url_for('index'))
    return render_template('index.html',
                           form=form,
                           name=session.get('name'),
                           current_time=datetime.utcnow(),
                           known=session.get('known', False)
                           )
    # 若没有设置它的值就返回get('known', False)默认值False
"""
程序可以把数据存储在用户会话中，在请求之间“记住”数据。用户会话是一种私有存
储，存在于每个连接到服务器的客户端中.
默认情况下，用户会话保存在客户端 cookie 中，使用设置的 SECRET_KEY 进
行加密签名。如果篡改了 cookie 中的内容，签名就会失效，会话也会随之失效
"""
# make_shell_context() 函数注册了程序、数据库实例以及模型,因此这些对象能直接导入 shell
def make_shell_context():
    return dict(app=app, db=db, User=User, Role =Role)
# 为shell命令添加一个上下文，make_context参数必须是一个返回字典的可调用对象，默认情况下，这只是一个返回Flask应用程序实例的字典
# make_shell_context()函数注册了程序、数据库实例以及模型,因此这些对象能直接导入shell
manager.add_command('shell',Shell(make_context=make_shell_context))


def send_email():
    msg = Message(subject="Hello World!",
                  sender='1241908493@qq.com',
                  recipients=["1430250645@qq.com"])
    msg.body = "testing"
    msg.html = "<b>testing</b>"
    thr = Thread(target=send_async_email, args=[app, msg])
    thr.start()
    return thr


# 异步发送邮件
def send_async_email(app, msg):
    """
    这里的with语句和** with open() as f一样，是Python提供的语法糖，可以为提供上下文环境省略简化一部分工作。
    这里就简化了其压栈和出栈操作，请求线程创建时，Flask会创建应用上下文对象，
    并将其压入flask._app_ctx_stack**的栈中，然后在线程退出前将其从栈里弹出。
    """
    with app.app_context():  # 手动创建应用上下文
        mail.send(msg)


if __name__ == '__main__':
    manager.run()

