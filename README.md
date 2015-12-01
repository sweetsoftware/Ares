# Ares
Python Remote Access Tool.

Ares is made of two main programs:

- A Command aNd Control server, which is a Web interface to administer the agents
- An agent program, which is run on the compromised host, and ensures communication with the CNC

The Web interface can be run on any server running Python. You need to install the cherrypy package.

The client is a Python program meant to be compiled as a win32 executable using pyinstaller.
It currently supports:
- remote cmd.exe shell
- persistence
- file upload/download
- screenshot
- key logging
