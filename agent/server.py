import urllib2

import settings


def tell(message):
    req = urllib2.Request(settings.SERVER_URL)
    req.add_header('X-Bot-Id', settings.BOT_ID)
    resp = urllib2.urlopen(req, message)
    return resp.read()


def hello():
    req = urllib2.Request(settings.SERVER_URL)
    req.add_header('X-Bot-Id', settings.BOT_ID)
    return urllib2.urlopen(req).read()
