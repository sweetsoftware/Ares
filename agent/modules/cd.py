import os


def run(directory):
    os.chdir(os.path.expandvars(os.path.expanduser(directory)))
    return "", None
