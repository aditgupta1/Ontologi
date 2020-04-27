import sqlite3

class SqlDB(object):
    def __init__(self, path):
        self.conn = sqlite3.connect(path)