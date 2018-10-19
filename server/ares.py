#!/usr/bin/env python2

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
from flask_script import Server

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
server = Server(host="0.0.0.0", port=443, ssl_crt='ares.cert', ssl_key='ares.key')
manager = Manager(app)
manager.add_command("runserver", server)


@app.after_request
def headers(response):
    response.headers["Server"] = "Ares"
    return response


@manager.command
def initdb():
    db.drop_all()
    db.create_all()
    db.session.commit()

    
if __name__ == '__main__':
    manager.run()
