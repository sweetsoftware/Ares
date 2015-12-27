import requests

import utils


def run(url):
    filename = url.split('/')[-1]
    r = requests.get(url, stream=True)
    with open(filename, 'wb') as f:
        for chunk in r.iter_content(chunk_size=8000):
            if chunk:
                f.write(chunk)
    utils.send_output("Downloaded: %s -> %s" % (url, filename), "")


def help():
    help_text = """
Usage: download http://example.com/filename
Downloads a file through HTTP.

"""
    return help_text
