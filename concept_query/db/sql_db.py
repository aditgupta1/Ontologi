import sqlite3

class SqlDB(object):
    def __init__(self, path):
        self.conn = sqlite3.connect(path)

        # Create table
        self.conn.execute('''CREATE TABLE IF NOT EXISTS PATTERNS
            (ID INTEGER PRIMARY KEY     AUTOINCREMENT,
            PATTERN        TEXT     NOT NULL,
            ENT            TEXT     NOT NULL,
            TIMESTAMP      INT      NOT NULL,
            FREQ           INT      NOT NULL);''')
        
    def execute(self, query, params=None):
        if params is None:
            return self.conn.execute(query)
        return self.conn.execute(query, params)

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()

    def delete(self):
        self.conn.execute("DROP TABLE IF EXISTS PATTERNS")
        print("SQL table deleted successfully!")
