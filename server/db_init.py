import sqlite3
import os

DBNAME = 'beta.db'

if os.path.exists(DBNAME):
    os.remove(DBNAME)
conn = sqlite3.connect(DBNAME)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE bots (
name text,
lastonline integer,
ip text,
os text,
UNIQUE(name))
""")

cursor.execute("""
CREATE TABLE output(
id integer primary key, 
date integer,
out text,
bot text,
FOREIGN KEY(bot) REFERENCES bots(name))
""")

cursor.execute("""
CREATE TABLE commands (
id integer primary key,
date integer,
cmd text,
sent integer,
bot text,
FOREIGN KEY(bot) REFERENCES bots(name))
""")

cursor.execute("""
CREATE TABLE users (
id integer primary key,
name text,
password text)
""")

conn.commit()
conn.close()
