# Ares
Ares is a Python Remote Access Tool.

__Warning: Only use this software according to your current legislation. Misuse of this software can raise legal and ethical issues which I don't support nor can be held responsible for.__

Ares is made of two main programs:

- A Command aNd Control server, which is a Web interface to administer the agents
- An agent program, which is run on the compromised host, and ensures communication with the CNC

The Web interface can be run on any server running Python. You need to install the cherrypy package.

The client is a Python program meant to be compiled as a win32 executable using [pyinstaller](https://github.com/pyinstaller/pyinstaller "pyinstaller"). It depends on the __requests__, __pythoncom__, __pyhook__ python modules and on __PIL__ (Python Imaging Library). 

It currently supports:
- remote cmd.exe shell
- persistence
- file upload/download
- screenshot
- key logging

## Installation

### Server

To install the server, first create the sqlite database:

__cd server/__

__python db_init.py__

If not installed, install the __cherrypy__ python package.

Then launch the server by issuing:
__python server.py__

By default, the server listens on http://localhost:8080

### Agent

The agent can be launched as a python script, but it is ultimately meant to be compiled as a win32 executable using [pyinstaller](https://github.com/pyinstaller/pyinstaller "pyinstaller").

First, install all the dependencies:

- requests

- pythoncom

- pyhook

- PIL

Then, configure agent/settings.py according to your needs:

SERVER_URL = URL of the CNC http server

BOT_ID = the (unique) name of the bot, leave empty to use hostname

DEBUG = should debug messages be printed to stdout ?

IDLE_TIME = time of inactivity before going in idle mode (the agent checks the CNC for commands far less often when idle).

REQUEST_INTERVAL = interval between each query to the CNC when active

PAUSE_AT_START = delay before contacting the server when launched (in seconds)

AUTO_PERSIST = should the agent be persistent by default

Finally, use pyinstaller to compile the agent into a single exe file:

__cd agent/python__

__pyinstaller --onefile --noconsole agent.py__

That's it ! You've got a fully standalone agent.


## Screenshots
### Bot list / mass execute
![Bot list](https://raw.githubusercontent.com/sweetsoftware/Ares/master/doc/sc_botlist.PNG "Bot list")
### Interactive shell
![Interactive shell](https://raw.githubusercontent.com/sweetsoftware/Ares/master/doc/sc_shell.PNG "Bot shell")

