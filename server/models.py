import random
import string
from datetime import datetime

from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class Agent(db.Model):
    __tablename__ = 'agents'
    id = db.Column(db.String(100), primary_key=True)
    display_name = db.Column(db.String(100))
    last_online = db.Column(db.DateTime())
    operating_system = db.Column(db.String(100))
    remote_ip = db.Column(db.String(100))
    geolocation = db.Column(db.String(100))
    cwd = db.Column(db.String(500))

    def __init__(self):
        uid = ''.join(random.choice(string.ascii_letters) for _ in range(20))
        while Agent.query.get(uid):
            uid = ''.join(random.choice(string.ascii_letters) for _ in range(20))
        self.set_id(uid)
        self.display_name = self.id

    def set_id(self, uid):
        self.id = uid
        db.session.commit()

    def push_command(self, cmdline):
        cmd = Command()
        cmd.agent = self
        cmd.cmdline = cmdline
        cmd.cwd = self.cwd
        if cmdline.startswith("upload"):
            cmd.waits_file=True
        db.session.add(cmd)
        db.session.commit()

    def rename(self, new_name):
        self.display_name = new_name
        db.session.commit()

    def is_online(self):
        return (datetime.now() - self.last_online).seconds < 30

    def set_cwd(self, cwd):
        self.cwd = cwd
        for cmd in self.commands.filter_by(executed=False):
            cmd.cwd = self.cwd


class Command(db.Model):
    __tablename__ = 'commands'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    agent_id = db.Column(db.Integer, db.ForeignKey('agents.id'))
    agent = db.relationship('Agent', backref=db.backref('commands', lazy='dynamic'))
    cmdline = db.Column(db.String(255))
    output = db.Column(db.Text())
    server_output = db.Column(db.Text(), default='')
    executed = db.Column(db.Boolean(), default=False)
    timestamp = db.Column(db.DateTime(), default=datetime.now)
    waits_file = db.Column(db.Boolean, default=False)
    cwd = db.Column(db.String(500))


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))
    salt = db.Column(db.String(100))
    last_login_time = db.Column(db.DateTime())
    last_login_ip = db.Column(db.String(100))
