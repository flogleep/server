# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import sys
import hashlib
from scrapy.exceptions import DropItem
from scrapy import log
import MySQLdb
import json
import time
import datetime
import pdb

DOUBLON_THRESHOLD = 120

DB_NAME = 'rer'
DB_USER = 'root'
DB_PWD = 'Quartz'
DB_HOST = 'localhost'

class StatusPipeline(object):
    def process_item(self, item, spider):

        if u'Train à quai' not in item['status'] and item['status'] != 'Inconnu':
            raise DropItem(
                u'Invalid status in [{0}, {1}, {2}]'.format(item['full_mission'],
                                                           item['status'],
                                                           item['station'])
            )
        return item

class FormatPipeline(object):
    def process_item(self, item, spider):

        if len(item['full_mission']) > 4:
	    item['mission'] = item['full_mission'][:4]
	    item['mission_id'] = int(item['full_mission'][4:])
	else:
	    item['mission'] = item['full_mission']
	    item['mission_id'] = ''
        return item

class SqlFilterPipeline(object):
    def __init__(self):
        self.conn = MySQLdb.connect(user=DB_USER,
                                    passwd=DB_PWD,
                                    db=DB_NAME,
                                    host=DB_HOST,
                                    charset="utf8",
                                    use_unicode=True)
        self.conn.autocommit(True)
        self.cursor = self.conn.cursor()

    def process_item(self, item, spider):

        try:
	    if item['mission_id'] == '':
                self.cursor.execute("""SELECT id, departure_time 
                                    FROM capture
                                    WHERE mission=%s
                                    AND station=%s
                                    ORDER BY departure_time DESC
                                    LIMIT 0, 1;""",
                                    (item['mission'].encode('utf-8'),
                                     item['station'].encode('utf-8')
                                     ))
	    else:
                self.cursor.execute("""SELECT id, departure_time 
                                    FROM capture
                                    WHERE mission=%s
				    AND mission_id=%s
                                    AND station=%s
                                    ORDER BY departure_time DESC
                                    LIMIT 0, 1;""",
                                    (item['mission'].encode('utf-8'),
				     item['mission_id'],
                                     item['station'].encode('utf-8')
                                     ))
            res = None
            for r in self.cursor:
                res = r
            item['item_id'] = None
            if res is not None:
                if (item['time'] - res[1]).total_seconds() < DOUBLON_THRESHOLD:
                    item['item_id'] = res[0]

        except MySQLdb.Error, e:
            print "Error %d: %s" % (e.args[0], e.args[1])

        return item

class SqlInsertPipeline(object):
    def __init__(self):
        self.conn = MySQLdb.connect(user=DB_USER,
                                    passwd=DB_PWD,
                                    db=DB_NAME,
                                    host=DB_HOST,
                                    charset="utf8",
                                    use_unicode=True)
        self.conn.autocommit(True)
        self.cursor = self.conn.cursor()

    def process_item(self, item, spider):

        try:
            if item['item_id'] is None:
                self.cursor.execute("""INSERT INTO
                                    capture (mission, mission_id, arrival_time, departure_time, station, status)
                                    VALUES (%s, %s, %s, %s, %s, %s);""",
                                    (item['mission'].encode('utf-8'),
				    item['mission_id'],
				    item['time'],
                                    item['time'],
                                    item['station'].encode('utf-8'),
				    item['status'].encode('utf-8')
                                    ))
                log.msg('New entry     : [{0}, {1:<40}, {2}, {3}]'.format(item['mission'],
                                                                     item['station'],
                                                                     item['time'],
								     item['status'].encode('utf-8')),
                         level=log.INFO)

            else:
                self.cursor.execute("""UPDATE capture
                                    SET departure_time=%s
                                    WHERE id=%s;""",
                                    (item['time'],
                                     item['item_id']
                                     ))
                log.msg('Updated entry : [{0}, {1:<40}, {2}, {3}]'.format(item['mission'],
                                                                     item['station'],
                                                                     item['time'],
								     item['status'].encode('utf-8')),
                         level=log.INFO)

        except MySQLdb.Error, e:
            print "Error %d: %s" % (e.args[0], e.args[1])

        return item

class JsonPipeline(object):
    def __init__(self):
        self.f = open('save.js', 'wb')

    def process_item(self, item, spider):

        line = json.dumps(dict(item)) + "\n"
        self.f.write(line)
        return item
