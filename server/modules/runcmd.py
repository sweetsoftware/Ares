import subprocess


def run(target, cmd):
    target["out"].put("runcmd")
    target["out"].put(cmd)
    output = target["in"].get()
    print output
    target["out"].put("")
