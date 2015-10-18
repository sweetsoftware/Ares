import os
import base64


FRAG_SIZE = 10000000


def run(target, filepath):
    print "[*] Uploading %s..." % filepath
    target["out"].put("upload")
    target["out"].put(filepath)
    fd = open(filepath, 'rb')
    while True:
        chunk = fd.read(FRAG_SIZE)
        if not chunk:
            break
        file_data = base64.b64encode(chunk)
        target["out"].put(file_data)
    fd.close()
    target["out"].put("END_OF_FILE")
    target["in"].get()
    target["out"].put("")
    print "[*] File uploaded !"
