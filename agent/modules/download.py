import os
import base64

import server


FRAG_SIZE = 10000000


def run():
    filepath = server.hello()
    if os.path.exists(filepath):
        fd = open(filepath, 'rb')
        while True:
            chunk = fd.read(FRAG_SIZE)
            if not chunk:
                break
            file_data = base64.b64encode(chunk)
            server.tell(file_data)
        fd.close()
        server.tell("END_OF_FILE")
