""" simplemysql, wrapper for mysql.connector

"""
#!/usr/bin/env python
# vim: fileencoding=utf-8: noexpandtab
# pylint: disable=invalid-name

from itertools import repeat
from collections import namedtuple
import mysql.connector as mysql

class SimpleMysql:
    """
    Define a SimpleMysql instance to connect with mysql.connector.

    ```
    Parameters:
    -----------
    db : str
        MySQL Database
    host : str
        MySQL Host
    user : str
        MySQL user
    passwd : str
        MySQL password
    """

    def __init__(self, **kwargs):
        self.conn = None
        self.cur = None
        self.conf = None

        self.conf = kwargs
        self.conf["keep_alive"] = kwargs.get("keep_alive", False)
        self.conf["charset"] = kwargs.get("charset", "utf8")
        self.conf["host"] = kwargs.get("host", "localhost")
        self.conf["port"] = kwargs.get("port", 3306)
        self.conf["autocommit"] = kwargs.get("autocommit", False)
        self.conf["ssl"] = kwargs.get("ssl", False)
        self.connect()

    def connect(self):
        """Connect to the mysql server"""

        try:
            if not self.conf["ssl"]:
                self.conn = mysql.connect(db=self.conf['db'],
                                          host=self.conf['host'],
                                          port=self.conf['port'],
                                          user=self.conf['user'],
                                          passwd=self.conf['passwd'],
                                          charset=self.conf['charset'])
            else:
                self.conn = mysql.connect(db=self.conf['db'],
                                          host=self.conf['host'],
                                          port=self.conf['port'],
                                          user=self.conf['user'],
                                          passwd=self.conf['passwd'],
                                          ssl=self.conf['ssl'],
                                          charset=self.conf['charset'])
            self.cur = self.conn.cursor()
            self.conn.autocommit = self.conf["autocommit"]
        except:
            print("MySQL connection failed")
            raise

    def getOne(self, table=None, fields='*', where=None, order=None, limit=(0, 1)):
        """Get a single result

            table = (str) table_name
            fields = (field1, field2 ...) list of fields to select
            where = ("parameterizedstatement", [parameters])
                    eg: ("id=%s and name=%s", [1, "test"])
            order = [field, ASC|DESC]
            limit = [from, to]
        """

        cur = self._select(table, fields, where, order, limit)
        result = cur.fetchone()

        row = None
        if result:
            fields = [f[0] for f in cur.description]
            row = zip(fields, result)

        return dict(row)

    def getAll(self, table=None, fields='*', where=None, order=None, limit=None):
        """Get all results

            table = (str) table_name
            fields = (field1, field2 ...) list of fields to select
            where = ("parameterizedstatement", [parameters])
                    eg: ("id=%s and name=%s", [1, "test"])
            order = [field, ASC|DESC]
            limit = [from, to]
        """

        cur = self._select(table, fields, where, order, limit)
        result = cur.fetchall()

        rows = None
        if result:
            fields = [f[0] for f in cur.description]
            rows = [dict(zip(fields, r)) for r in result]

        return rows

    def lastId(self):
        """Get the last insert id"""
        return self.cur.lastrowid

    def lastQuery(self):
        """Get the last executed query"""
        try:
            return self.cur.statement
        except AttributeError:
            return self.cur._last_executed

    def leftJoin(self, tables=(), fields=(), join_fields=(), where=None, order=None, limit=None):
        """Run an inner left join query

            tables = (table1, table2)
            fields = ([fields from table1], [fields from table 2])  # fields to select
            join_fields = (field1, field2)  # fields to join. field1 belongs to table1 and field2 belongs to table 2
            where = ("parameterizedstatement", [parameters])
                    eg: ("id=%s and name=%s", [1, "test"])
            order = [field, ASC|DESC]
            limit = [limit1, limit2]
        """

        cur = self._select_join(tables, fields, join_fields, where, order, limit)
        result = cur.fetchall()

        rows = None
        if result:
            Row = namedtuple("Row", [f[0] for f in cur.description])
            rows = [Row(*r) for r in result]

        return rows

    def insert(self, table:str, data: dict):
        """Insert a single record of data into a table

        ```
        Parameters:
        -----------
        table : str
            Table name to insert data into
        data : dict
            Dictionary containing data to insert

        Example:
        ----------
            > simplemysqlobj.insertBatch("table_name", {"colA" : 1, "colB" : 2})

        """

        query = self._serialize_insert(data)
        sql = f"INSERT INTO {table} ({query[0]}) VALUES({query[1]})"

        return self.query(sql, tuple(data.values())).rowcount

    def insertBatch(self, table: str, data: list):
        """Insert multiple records of data into a table

        ```
        Parameters:
        -----------
        table : str
                Table name to insert data into
        data : list
                List of dict records to insert

        Example:
        ----------
            > simplemysqlobj.insertBatch("table_name", [{"colA" : 1, "colB" : 2},
                                                        {"colA" : 3, "colB" : 4}])

        """

        query = self._serialize_batch_insert(data)
        sql = f"INSERT INTO {table} ({query[0]}) VALUES {query[1]}"

        flattened_values = [v for sublist in data for k, v in iter(sublist.items())]

        return self.query(sql, flattened_values).rowcount

    def update(self, table, data, where=None):
        """Insert a record"""

        query = self._serialize_update(data)

        sql = f"UPDATE {table} SET {query}"

        if where and len(where) > 0:
            sql += f" WHERE {where[0]}"

        values = tuple(data.values())

        return self.query(
            sql, values + where[1] if where and len(where) > 1 else values
        ).rowcount

    def insertOrUpdate(self, table, data, keys):
        insert_data = data.copy()

        data = {k: data[k] for k in data if k not in keys}

        insert = self._serialize_insert(insert_data)
        update = self._serialize_update(data)

        sql = "INSERT INTO %s (%s) VALUES(%s) ON DUPLICATE KEY UPDATE %s" % (table, insert[0], insert[1], update)

        return self.query(sql, tuple(insert_data.values()) + tuple(data.values())).rowcount

    def delete(self, table, where=None):
        """Delete rows based on a where condition"""

        sql = "DELETE FROM %s" % table

        if where and len(where) > 0:
            sql += " WHERE %s" % where[0]

        return self.query(sql, where[1] if where and len(where) > 1 else None).rowcount

    def addIndex(self, table, index_name, fields=[]):
        sanitized_fields = ','.join(fields)
        sql = 'ALTER TABLE %s ADD INDEX %s (%s)' % (table, index_name, sanitized_fields)

        return self.query(sql)

    def dropIndex(self, table_name, index_name):
        sql = 'ALTER TABLE %s DROP INDEX %s' % (table_name, index_name)

        return self.query(sql)

    def query(self, sql, params=None):
        """Run a raw query"""

        # check if connection is alive. if not, reconnect

        try:
            self.cur.execute(sql, params)
        except mysql.OperationalError as e:
            # mysql timed out. reconnect and retry once
            if e[0] == 2006:
                self.connect()
                self.cur.execute(sql, params)
            else:
                raise
        except:
            print("Query failed")
            raise

        return self.cur

    def callProc(self, procedure_name: str, args=()):
        """ Call a procedure in MySQL

        Parameters:
        -----------
        procedure_name : str
            Name of procedure to call in MySQL
        args : tuple
            Parameters to pass, leave empty for no procedures

        """
        self.cur.callproc(procedure_name, args)

    def commit(self):
        """Commit a transaction (transactional engines like InnoDB require this)"""
        return self.conn.commit()

    def is_open(self):
        """Check if the connection is open"""
        return self.conn.open

    def end(self):
        """Kill the connection"""
        self.cur.close()
        self.conn.close()

    def _serialize_insert(self, data):
        """Format insert dict values into strings"""
        keys = ",".join(data.keys())
        vals = ",".join(["%s" for k in data])

        return [keys, vals]

    def _serialize_batch_insert(self, data):
        """Format insert dict values into strings"""

        keys = ",".join(data[0].keys())
        v = "(%s)" % ",".join(tuple("%s".rstrip(',') for v in range(len(data[0]))))
        l = ','.join(list(repeat(v, len(data))))

        return [keys, l]

    def _serialize_update(self, data):
        """Format update dict values into string"""
        return "=%s,".join(data.keys()) + "=%s"

    def _select(self, table=None, fields=(), where=None, order=None, limit=None):
        """Run a select query"""

        sql = "SELECT %s FROM `%s`" % (",".join(fields), table)

        # where conditions
        if where and len(where) > 0:
            sql += " WHERE %s" % where[0]

        # order
        if order:
            sql += " ORDER BY %s" % order[0]

            if len(order) > 1:
                sql += " %s" % order[1]

        # limit
        if limit:
            sql += " LIMIT %s" % limit[0]

            if len(limit) > 1:
                sql += ", %s" % limit[1]

        return self.query(sql, where[1] if where and len(where) > 1 else None)

    def _select_join(self, tables=(), fields=(), join_fields=(), where=None, order=None, limit=None):
        """Run an inner left join query"""

        fields = [tables[0] + "." + f for f in fields[0]] + \
                 [tables[1] + "." + f for f in fields[1]]

        sql = "SELECT %s FROM %s LEFT JOIN %s ON (%s = %s)" % \
              (",".join(fields),
               tables[0],
               tables[1],
               tables[0] + "." + join_fields[0],
               tables[1] + "." + join_fields[1]
               )

        # where conditions
        if where and len(where) > 0:
            sql += " WHERE %s" % where[0]

        # order
        if order:
            sql += " ORDER BY %s" % order[0]

            if len(order) > 1:
                sql += " " + order[1]

        # limit
        if limit:
            sql += " LIMIT %s" % limit[0]

            if len(limit) > 1:
                sql += ", %s" % limit[1]

        return self.query(sql, where[1] if where and len(where) > 1 else None)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.end()
