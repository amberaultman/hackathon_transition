__author__ = 'Sean Paley'
import psycopg2
import psycopg2.extras
from Config import Config
import logging

def fetchone(dsn, sql, params=None):
    with psycopg2.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchone()


def fetchall(dsn, sql, params=None):
    rows = []

    with PGReader(dsn, sql, params) as rdr:
        for row in rdr:
            dict_row = {}
            dict_row.update(row)
            rows.append(dict_row)
    return rows


def retrieve(dsn, sql, params=None):
    with PGReader(dsn=dsn, sql=sql, params=params) as rdr:
        for r in rdr:
            #just return the first one
            return r


class PGReader(object):
    def __init__(self, dsn, sql, params=None, field_dict=None, server_cursor=False, print_params=True):
        self.dsn = dsn
        self.sql = sql
        self.params = params
        self.field_dict = field_dict
        self.server_cursor = server_cursor
        self.print_params = print_params
        self.cursor = 0
        self.conn = None
        self.logger = logging.getLogger("PGReader")

    def __enter__(self):
        self.conn = psycopg2.connect(self.dsn)
        return self

    def __exit__(self, type, value, traceback):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

    def __iter__(self):
        if self.server_cursor:
            #for some reason this is really slow.  implementing it directly seems to improve things, but then it doesn't support dict
            self.cursor = self.conn.cursor('server_cursor', cursor_factory=psycopg2.extras.DictCursor)
            self.cursor.itersize=2000
        else:
            self.cursor = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        self.logger.debug(self.sql)
        if self.params:
            self.logger.debug(self.params)
        self.cursor.execute(self.sql, self.params)
        return self

    def next(self):
        row = self.cursor.fetchone()
        if not row: raise StopIteration()

        if not self.field_dict:
            return self.modify(row)

        values = {}
        for k, v in self.field_dict.iteritems():
            if hasattr(v, '__call__'):
                values[k] = v(row)
            else:
                values[k] = row[v]
        return values

    def modify(self, row):
        return row



if __name__ == "__main__":
    print retrieve(Config.DATABASE_URI, "SELECT 'yo' as joe")['joe']
    pass