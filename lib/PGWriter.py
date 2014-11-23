__author__ = 'Sean Paley'
import psycopg2
from Config import Config
import re
from psycopg2.extensions import adapt, register_adapter, AsIs
from os import path
import datetime
import logging


class PGWriter(object):
    def __init__(self, dsn, always_load_files=True, auto_commit=True):
        self.dsn = dsn
        self.table_dicts = self.get_table_dicts()
        self.always_load_files = always_load_files
        self.logger = logging.getLogger("PGWriter")
        self.auto_commit = auto_commit

    def deploy(self):
        tables_created = self.create_tables()
        if self.always_load_files or tables_created:
            self.load_files()

    def __enter__(self):
        self.conn = psycopg2.connect(self.dsn)
        self.insert_cursor = self.conn.cursor()
        return self

    def __exit__(self, type, value, traceback):
        if self.auto_commit and self.conn:
            self.commit()

        if self.insert_cursor: self.insert_cursor.close
        if self.conn: self.conn.close

    def get_table_dicts(self):
        raise NotImplementedError("implement get_table_dicts")

    def get_files(self):
        return None, []

    def create_table_sql(self, table_dict, name=None, temp=False):
        primary_key = table_dict.get("primary_key")

        return "CREATE %s TABLE %s (%s);" % ("TEMPORARY" if temp else "",
                                             name if name else table_dict["name"],
                                             ", ".join("\"%s\" %s %s" % (tup[0], tup[1], "primary key" if tup[0] == primary_key else "") for tup in table_dict["columns"]))

    def create_tables(self):
        tables_created = False

        cur = self.conn.cursor()
        for table in self.table_dicts:
            reloadsql = ""
            create = False

            if table.get("recreate", ""):
                self.logger.info("%s: dropping table" % (table["name"]))
                cur.execute("DROP TABLE IF EXISTS %s CASCADE;" % (table["name"]))
                create = True
            else:
                cur.execute("""SELECT column_name, udt_name
                    FROM INFORMATION_SCHEMA.COLUMNS WHERE table_name = %(table)s""", {"table": table["name"]})

                current_columns = cur.fetchall()
                desired_columns = table["columns"]
                compare_columns = [(x, y if y.lower() != "bigserial" else "int8") for (x, y) in desired_columns]

                if len(current_columns) == 0:
                    create = True

                elif cmp(current_columns, compare_columns) != 0:
                    save_table = table["name"] + "_save"
                    self.logger.info("%s: renaming table" % (table["name"]))
                    cur.execute("DROP TABLE IF EXISTS %s CASCADE;" % (save_table))
                    cur.execute("ALTER TABLE %s RENAME TO %s;" % (table["name"], save_table))

                    desired_set = set([x for (x, y) in desired_columns])
                    reload_columns_str = ", ".join(['"%s"' % column for (column, y) in current_columns if column in desired_set])
                    #print reload_columns_str
                    reloadsql = "INSERT INTO %s (%s) SELECT %s FROM %s" % (table["name"], reload_columns_str, reload_columns_str, save_table)
                    #print reloadsql
                    create = True

            if create:
                sql = self.create_table_sql(table)
                #print sql
                self.logger.info("%s: creating table" % (table["name"]))
                cur.execute(sql)

            if reloadsql:
                self.logger.info("%s: reloading table" % (table["name"]))
                cur.execute(reloadsql)

                #need to reset the sequence numbers
                primary_key = table.get("primary_key")
                if primary_key:
                    cur.execute("SELECT COALESCE(MAX(%s) + 1, 1) FROM %s" % (primary_key, table["name"]))
                    pk_restart = cur.fetchone()[0]

                    cur.execute("""SELECT column_default
                        FROM INFORMATION_SCHEMA.COLUMNS WHERE table_name = %(table)s AND column_name = %(column)s""", {"table": table["name"], "column": primary_key})
                    pk_default = cur.fetchone(  )[0]
                    pk_seq = re.search("'(.*)'", pk_default).group(1)

                    cur.execute("ALTER SEQUENCE %s RESTART WITH %s" % (pk_seq, pk_restart))

            self.conn.commit()
            if create:
                tables_created = True
        cur.close
        return tables_created

    def load_files(self):
        (p, files) = self.get_files()
        if not p:
            return

        d = path.dirname(path.realpath(p))

        with self.conn.cursor() as cur:
            for f in files:
                sqlfile = path.join(d, f)
                self.logger.info("Executing sql file %s" % sqlfile)
                #sql = codecs.open(sqlfile, encoding='utf-8').read().decode()
                sql = open(path.join(d, f)).read().decode(errors='ignore')
                cur.execute(sql)

        pass

    def get_table_dict(self, table):
        for table_dict in self.table_dicts:
            if table_dict["name"] == table:
                return table_dict

    def get_columns(self, table):
        columns = []
        for column in self.get_table_dict(table)["columns"]:
            columns.append(column[0])
        return columns





    def load(self, table, reader, batch_size=0, table_name=None, prepare=True, prepare_params=None):
        self.logger.info("%s: starting load" % table)
        if prepare:
            self.prepare_for_load(table, prepare_params)
        columns = self.get_columns(table)
        rows = 0
        for r in reader:
            self.insert(table, r, columns, table_name=table_name)
            rows += 1
            if batch_size and rows % batch_size == 0:
                self.commit()

        self.commit()
        self.logger.info("%s: loaded %s rows" % (table, rows))

    def insert(self, table, insert_dict, columns=None, table_name=None, commit=False, get_serial=False):
        sql_columns = ""
        sql_values = ""

        if not columns: columns = self.get_columns(table)

        insert_dict = self.convert_data_types(insert_dict)

        for column in columns:
            v = insert_dict.get(column)
            if v is not None:
                sql_columns += (", " if sql_columns else "") + ('"%s"' % column)
                sql_values += (", " if sql_values else "") + ("%%(%s)s" % column)

        sql = "INSERT INTO %s (%s) VALUES (%s); %s" % (table_name if table_name else table, sql_columns, sql_values,
                                                   "SELECT lastval()" if get_serial else "")
        #if sql.find("common_log") < 0:
        #    print sql
        self.logger.debug(sql)
        self.insert_cursor.execute(sql, insert_dict)
        ret = None
        if get_serial:
            ret = self.insert_cursor.fetchone()[0]
        if commit:
            self.commit()
        return ret

    def update(self, table, update_dict, id_column=None, columns=None):
        sql_set = ""

        table_dict = self.get_table_dict(table)

        if not id_column:
            id_column = table_dict["primary_key"]

        if not columns: columns = table_dict["columns"]

        update_dict = self.convert_data_types(update_dict)
        for (column, column_type) in columns:
            v = update_dict.get(column)
            if v is not None and column != id_column:
                sql_set += (", " if sql_set else "") + ("%s = %%(%s)s" % (column, column))

        where = "%s = %%(%s)s" % (id_column, id_column)

        sql = "UPDATE %s SET %s WHERE %s" % (table, sql_set, where)
        #print sql
        self.logger.debug(sql)
        self.insert_cursor.execute(sql, update_dict)

    def delete(self, table, id_value, id_column=None):
        sql_set = ""

        table_dict = self.get_table_dict(table)

        if not id_column:
            id_column = table_dict["primary_key"]

        sql = "DELETE FROM %s WHERE %s = %%(%s)s" % (table, id_column, id_column)
        self.logger.debug(sql)
        self.insert_cursor.execute(sql, {id_column: id_value})

    def convert_data_types(self, values_dict):
        v = values_dict.copy()
        for key, value in v.iteritems():
            if isinstance(value, bool):
                v[key] = 'Y' if value else 'N'
        return v

    def execute(self, sql, name=None, params=None, commit=True):
        if name:
            self.logger.info("%s: starting" % name)
        self.logger.debug(sql)
        self.insert_cursor.execute(sql, params)
        count = self.insert_cursor.rowcount
        if commit:
            self.commit()
        if name:
            self.logger.debug("%s: updated %s rows" % (name, count))
        return count


    def remove_duplicates(self, table, partition_by_columns, order_by_col, primary_key=None, exclude_partition_by=False):
        table_dict = self.get_table_dict(table)
        primary_key = primary_key if primary_key else table_dict.get("primary_key")

        if exclude_partition_by:
            partition_by_columns = [x for x in self.get_columns(table) if x not in partition_by_columns]

        partition_by = ",\n".join(['"%s"' % col for col in partition_by_columns])

        sql = """
            DELETE FROM "%(table)s"
            WHERE "%(primary_key)s" IN
                (
                    SELECT "%(primary_key)s"
                    FROM
                        (
                            SELECT "%(primary_key)s", ROW_NUMBER() OVER (PARTITION BY %(partition_by)s ORDER BY "%(order_by)s" DESC) as rownum
                            FROM "%(table)s"
                        ) x
                    WHERE rownum > 1
                )
                """ % \
            {
                "table": table,
                "primary_key": primary_key,
                "partition_by": partition_by,
                "order_by": order_by_col
            }
        #print sql
        self.execute(sql, name=table + " duplicates", commit=True)

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    @staticmethod
    def generate_columns(row_dict):
        result = []
        for k, v in row_dict.iteritems():
            pgtype = "text"
            if isinstance(v, int):
                pgtype = "int4"
            elif isinstance(v, long):
                pgtype = "int8"
            elif isinstance(v, datetime.datetime):
                pgtype = "timestamp"
            elif isinstance(v, datetime.date):
                pgtype = "date"
            elif isinstance(v, datetime.time):
                pgtype = "time"
            elif isinstance(v, float):
                pgtype = "numeric"
            result.append((k, pgtype))
        return sorted(result)