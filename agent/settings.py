import ConfigParser
import os
import io


BUILTIN_CONFIG = """
[General]
UID = anonymous
SERVER = http://localhost:5000
HELLO_INTERVAL = 2
IDLE_TIME = 20
"""


class Settings(object):
    """ Manages agent's settings, such as CNC address, UID, etc ..."""
    def __init__(self):
        self.config = ConfigParser.RawConfigParser()
        self.config.readfp(io.BytesIO(BUILTIN_CONFIG))

    def get(self, key):
        return self.config.get('General', key)

    def set(self, key, val):
        self.config.set('General', key, val)

    def save(self, local_path):
        with open(local_path, 'w') as f:
            self.config.write(f)

    def load_from_file(self, local_path):
        self.config.read(local_path)
