import random
import string
from functools import wraps
import hashlib
from datetime import datetime

from flask import Blueprint
from flask import abort
from flask import request
from flask import redirect
from flask import render_template
from flask import session
from flask import url_for
from flask import flash
from flask import send_from_directory
from flask import current_app

from models import db
from models import Agent
from models import Command
from models import User


def hash_and_salt(password):
    password_hash = hashlib.sha256()
    salt = ''.join(random.choice(string.ascii_letters + string.digits) for i in range(8))
    password_hash.update(salt + request.form['password'])
    return password_hash.hexdigest(), salt


def require_admin(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'username' in session and session['is_admin']:
            return func(*args, **kwargs)
        else:
            flash("user is not an admin")
            return redirect(url_for('webui.login'))
    return wrapper

def require_user(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'username' in session:
            return func(*args, **kwargs)
        else:
            return redirect(url_for('webui.login'))
    return wrapper


webui = Blueprint('webui', __name__, static_folder='static', static_url_path='/static/webui', template_folder='templates')


@webui.route('/')
@require_user
def index():
    return render_template('index.html')


@webui.route('/login', methods=['GET', 'POST'])
def login():
    if not User.query.filter_by(is_admin=True).first():
        #Comes Here if there is no admin user in the table
        if request.method == 'POST':
            if 'password' in request.form:
                password_hash, salt = hash_and_salt(request.form['password'])
                if not User.query.filter_by(username=request.form['username']).first():
                    new_user = User()
                    new_user.username = request.form['username']
                    new_user.password = password_hash
                    new_user.salt = salt
                    new_user.is_admin = True
                    db.session.add(new_user)
                    db.session.commit()
                    flash('User set successfully. Please log in.')
                else:
                    flash('User Already Present')
                return redirect(url_for('webui.login'))
        return render_template('create_user.html',show_checkbox=False)
    #when there is an admin in the table
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user != None:
            if request.form['password'] and request.form['username']:
                    password_hash = hashlib.sha256()
                    password_hash.update(user.salt + request.form['password'])
                    if user.password == password_hash.hexdigest():
                        session['username'] = request.form['username']
                        session['is_admin'] = user.is_admin
                        last_login_time =  user.last_login_time
                        last_login_ip = user.last_login_ip
                        user.last_login_time = datetime.now()
                        user.last_login_ip = request.remote_addr
                        db.session.commit()
                        flash('Logged in successfully.') 
                        if last_login_ip:
                            flash('Last login from ' + last_login_ip + ' on ' + last_login_time.strftime("%d/%m/%y %H:%M"))
                        return redirect(url_for('webui.index'))
                    else:
                        flash('Wrong passphrase')
    return render_template('login.html')

@webui.route('/adduser',methods=['GET','POST'])
@require_admin
def add_user():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if 'password' in request.form and not user:
            password_hash, salt = hash_and_salt(request.form['password'])
            new_user = User()
            new_user.username = request.form['username']
            new_user.password = password_hash
            new_user.salt = salt
            new_user.is_admin = 'is_admin' in request.form
            db.session.add(new_user)
            db.session.commit()
            flash('User set successfully. Please log in.')
            return redirect(url_for('webui.index'))
        else:
            flash("Username already present")
    return render_template('create_user.html',show_checkbox=True)



@webui.route('/passchange', methods=['GET', 'POST'])
@require_user
def change_password():
    if request.method == 'POST':
        if 'password' in request.form:
            admin_user = User.query.filter_by(username=session['username']).first()
            password_hash, salt = hash_and_salt(request.form['password'])
            admin_user.password = password_hash
            admin_user.salt = salt
            db.session.add(admin_user)
            db.session.commit()
            flash('Password reset successfully. Please log in.')
            return redirect(url_for('webui.login'))
    return render_template('create_password.html')


@webui.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('is_admin', None)
    flash('Logged out successfully.')
    return redirect(url_for('webui.login'))


@webui.route('/agents')
@require_user
def agent_list():
    agents = Agent.query.order_by(Agent.last_online.desc())
    return render_template('agent_list.html', agents=agents)


@webui.route('/agents/<agent_id>')
@require_user
def agent_detail(agent_id):
    agent = Agent.query.get(agent_id)
    if not agent:
        abort(404)
    return render_template('agent_detail.html', agent=agent)


@webui.route('/agents/rename', methods=['POST'])
@require_user
def rename_agent():
    if 'newname' in request.form and 'id' in request.form:
        agent = Agent.query.get(request.form['id'])
        if not agent:
            abort(404)
        agent.rename(request.form['newname'])
    else:
        abort(400)
    return ''


@webui.route('/uploads/<path:path>')
def uploads(path):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], path)
