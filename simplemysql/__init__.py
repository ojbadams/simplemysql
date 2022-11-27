"""
    A very simple wrapper for mysql (mysql-connector)

    Methods:
        getOne() - get a single row
        getAll() - get all rows
        lastId() - get the last insert id
        lastQuery() - get the last executed query
        insert() - insert a row
        insertBatch() - Batch Insert
        insertOrUpdate() - insert a row or update it if it exists
        update() - update rows
        delete() - delete rows
        query()  - run a raw sql query
        leftJoin() - do an inner left join query and get results

    License: GNU GPLv2

    Kailash Nadh, http://nadh.in
    May 2013

    Updated by: Milosh Bolic
    June 2019
"""
from .simplemysql import SimpleMysql