import os
import base64

import server


def run():
    filepath = server.hello()
    localfile = os.path.basename(filepath)
    while os.path.exists(localfile):
        localfile = "up_" + localfile
    fd = open(localfile, 'wb')
    while True:
        file_data = server.hello()
        if file_data == "END_OF_FILE":
            break
        chunk = base64.b64decode(file_data)
        fd.write(chunk)
    fd.close()
    server.tell('')
