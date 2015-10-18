import os
import base64


def run(target, operation):
    target["out"].put("keylogger")
    target["out"].put(operation)
    print target["in"].get()
    target["out"].put("")
