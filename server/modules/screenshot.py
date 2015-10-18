import os
import base64
import string
import random

import download


def run(target):
    print "[*] Taking screenshot..."
    target["out"].put("screenshot")
    filepath = target["in"].get()
    download.run(target, filepath)
