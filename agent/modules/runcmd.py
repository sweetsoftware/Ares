import os


def run(cmd):
    stdin, stdout, stderr = os.popen3(cmd)
    output = stdout.read() + stderr.read()
    return output, None
