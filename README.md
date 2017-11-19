# Ares

Ares is a Python Remote Access Tool.

__Warning: Only use this software according to your current legislation. Misuse of this software can raise legal and ethical issues which I don't support nor can be held responsible for.__

Ares is made of two main programs:

- A Command aNd Control server, which is a Web interface to administer the agents
- An agent program, which is run on the compromised host, and ensures communication with the CNC

The Web interface can be run on any server running Python. The agent can be compiled to native executables using **pyinstaller**.

## Server

## Setup

Install the Python requirements for the server:

```
cd server
pip install -r server_requirements.txt
```

Initialize the database:

```
./ares.py initdb
```

## Usage

Run the server:

```
gunicorn ares:app -b 0.0.0.0:8080 --threads 20
```

The server should now be accessible on http://localhost:8080

## Agent

### Setup

Install the Python requirements for the agent:

```
cd agent
pip install -r agent_requirements.txt
```

In order to compile Windows agents on Linux, setup wine (optional):

```
./wine_setup.sh
```

### Run

Run the Python agent:

```
./agent.py
```

By default, the agent tries to reach a CnC on http://localhost:8080

To build a new agent to a standalone binary, use the following command:

```
./ares.py buildagent <program_name> <server_url> <platform>
``` 

Where:
    - program_name is the resulting executable name
    - server_url should be set to the CnC server's URL
    - the platform is either Windows or Linux.

e.g.

```
./ares.py buildagent testagent http://localhost:8080 Linux
```

The **buildagent** command supports the following optional arguments:

```
-h <delay> time delay (in seconds) between each contact with the CnC (to pull new commands)
-m <max_failed_attempts> maximum number of failed connections (over that limit, the agent self-destructs)
-i <idel_time> time (in seconds) after which the agent goes to sleep if no new command is received (when the agent sleeps, it tries to pull commands less often)
-p add this flag to make the agent persistent by default
```

Build agents are stored in server/agents/.

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

python <command|file>
Runs a Python command or local file.

persist
Installs the agent.

clean
Uninstall the agent.

exit
Kills the agent.

help
This help.
```
