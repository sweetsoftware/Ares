import requests

import settings


def send_output(output):
    requests.post(settings.SERVER_URL + "/api/report", {'botid': settings.BOT_ID, 'output': output})
