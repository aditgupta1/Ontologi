import sqlite3
import mysql.connector
import time

class SqlDB(object):
    def __init__(self, dbtype='sqlite3', **kwargs):
        """
        MySQL
            Password is given by the user at the time of installing the MySQL 
            database. If you are using root then you won’t need the password.
        
        ref: https://pynative.com/python-mysql-insert-data-into-database-table/
        """

        self.dbtype = dbtype

        if dbtype == 'sqlite3':
            print("Connecting sqlite3 database...")
            assert 'path' in kwargs.keys()

            self.conn = sqlite3.connect(kwargs['path'])

            # Create table
            self.conn.execute('''CREATE TABLE IF NOT EXISTS PATTERNS
                (ID INTEGER PRIMARY KEY     AUTOINCREMENT,
                PATTERN        TEXT     NOT NULL,
                ENT            TEXT     NOT NULL,
                TIMESTAMP      INT      NOT NULL,
                FREQ           INT      NOT NULL);''')
            print("PATTERNS table created successfully!")
        elif dbtype == 'mysql':
            print("Connecting MySQL database...")
            assert 'host' in kwargs.keys()
            assert 'user' in kwargs.keys()
            assert 'database' in kwargs.keys()

            self.conn = mysql.connector.connect(host=kwargs['host'], 
                user=kwargs['user'], database=kwargs['database'])
            
            print("MySQL connected:", self.conn.is_connected())

            self.cursor = self.conn.cursor()
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS PATTERNS
                (ID INT PRIMARY KEY     AUTO_INCREMENT,
                PATTERN        TEXT     NOT NULL,
                ENT            TEXT     NOT NULL,
                TIMESTAMP      INT      NOT NULL,
                FREQ           INT      NOT NULL);''')
            print("PATTERNS table created successfully!")
        else:
            raise ValueError(dbtype + ' database not supported')

    @classmethod
    def fromconfig(cls, config):
        if config['DBTYPE'] == 'sqlite3':
            return cls(dbtype=config['DBTYPE'], path=config['PATH'])
        elif config['DBTYPE'] == 'mysql':
            return cls(dbtype=config['DBTYPE'], 
                host=config['HOST'],
                user=config['USER'],
                database=config['DATABASE'])

        raise ValueError(config['DBTYPE'] + ' database not supported')
        
    def execute(self, query, params=None):
        if params is None:
            if self.dbtype == 'sqlite3':
                return self.conn.execute(query)
            elif self.dbtype == 'mysql':
                self.cursor.execute(query)
                return self._mysql_fetch()
            else:
                raise ValueError(self.dbtype + ' database not supported')
        
        if self.dbtype == 'sqlite3':
            return self.conn.execute(query, params)
        elif self.dbtype == 'mysql':
            # MySQL parameterized arguments uses %s instead of ?
            query = query.replace('?', '%s')
            self.cursor.execute(query, params)
            return self._mysql_fetch()
        
        raise ValueError(self.dbtype + ' database not supported')

    def executemany(self, query, params, max_retries=4):
        if self.dbtype == 'sqlite3':
            i = 0
            while i < max_retries:
                try:
                    return self.conn.executemany(query, params)
                except sqlite3.OperationalError:
                    time.sleep(0.5)
                    i += 1
            return
        
        elif self.dbtype == 'mysql':
            # MySQL parameterized arguments uses %s instead of ?
            query = query.replace('?', '%s')
            i = 0
            while i < max_retries:
                try:
                    self.cursor.executemany(query, params)
                    return self._mysql_fetch()
                except mysql.connector.errors.DatabaseError:
                    time.sleep(0.5)
                    i += 1

        raise ValueError(self.dbtype + ' database not supported')

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()

        if self.dbtype == 'mysql':
            self.cursor.close()

    def delete(self):
        if self.dbtype == 'sqlite3':
            self.conn.execute("DROP TABLE IF EXISTS PATTERNS")
        elif self.dbtype == 'mysql':
            self.cursor.execute("DROP TABLE IF EXISTS PATTERNS")
        else:
            raise ValueError(self.dbtype + ' database not supported')

        print("SQL table deleted successfully!")

    def _mysql_fetch(self):
        try:
            return self.cursor.fetchall()
        except mysql.connector.errors.InterfaceError:
            return None