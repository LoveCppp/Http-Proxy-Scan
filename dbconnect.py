#!/usr/bin/env python
#coding:utf-8

import MySQLdb


def connection():
    try:
        conn = MySQLdb.connect(host='127.0.0.1',user='root',passwd='root',db='proxy')
        conn.autocommit(1)
    except Exception,e:
        return e
    return conn