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

## Screenshots
### Bot list / mass execute
![Bot list](https://raw.githubusercontent.com/sweetsoftware/Ares/master/doc/sc_botlist.PNG "Bot list")
### Interactive shell
![Interactive shell](https://raw.githubusercontent.com/sweetsoftware/Ares/master/doc/sc_shell.PNG "Bot shell")

