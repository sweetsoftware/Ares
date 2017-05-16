#!/usr/bin/env python

import random
import string
import hashlib
from functools import wraps
import datetime

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


if __name__ == '__main__':
    manager.run()
