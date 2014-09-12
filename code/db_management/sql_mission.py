import xlrd
import pdb
import MySQLdb
from contextlib import closing

PATH = './west_summer.xls'

DB_USER = 'root'
DB_PWD = 'Quartz'
DB_HOST = 'localhost'
DB_NAME = 'rer'

connection = MySQLdb.connect(user=DB_USER,
        passwd=DB_PWD,
        db=DB_NAME,
        host=DB_HOST,
        charset="utf8",
        use_unicode=True)
connection.autocommit(True)

wb = xlrd.open_workbook(PATH)
sh = wb.sheet_by_name(wb.sheet_names()[0])

missions_added = []
station_indexes = sh.col_values(0)

for colnum in xrange(1, sh.ncols):
    c = sh.col_values(colnum)

    m_name = c[0]
    if m_name not in missions_added:
        m_id = -1
        with closing(connection.cursor()) as cursor:
            cursor.execute("""SELECT id
                    FROM missions
                    WHERE name=%s;""",
                    m_name)
            for r in cursor:
                m_id = r[0]
        if m_id == -1:
            if len(m_name) > 4:
                pdb.set_trace()
            with closing(connection.cursor()) as cursor:
                cursor.execute("""INSERT INTO missions
                (name, line, direction)
                VALUES
                (%s, 'A', -1);""",
                m_name)
                cursor.execute("""SELECT id
                    FROM missions
                    WHERE name=%s;""",
                    m_name)
                for r in cursor:
                    m_id = r[0]
            query = ''
            pos = 0
            for i in xrange(1, len(c)):
                if c[i] != '':
                    query += """INSERT INTO missions_description
                    (mission_id, station_id, position, time)
                    VALUES
                    ({0}, {1}, {2}, {3})
                    ;""".format(m_id, station_indexes[i], pos, c[i])
                    pos += 1
            with closing(connection.cursor()) as cursor:
                cursor.execute(query)
        missions_added.append(m_name)
