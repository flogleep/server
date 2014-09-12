"""Controller for gathering and chaining trains."""

import train_objects as tr
import graphic_train as gt
import chain as ch
import pickle
import os
import pdb
import MySQLdb
from contextlib import closing
import datetime


DB_USER = 'root'
DB_PWD = 'Quartz'
DB_HOST = 'localhost'
DB_NAME = 'rer'
HISTORIC_LENGTH = 2 * 60 * 60
LINE_NAME = 'A'
START_DATE = datetime.datetime(2014, 8, 8, 4, 0, 0)


def load_line(line_name, connection):
    """Return a Line object from the database."""
    
    print "Loading line...",
    stations = []
    operators = []

    with closing(connection.cursor()) as cursor:
        try:
            cursor.execute("""SELECT name, operator
                           FROM stations
                           WHERE line=%s;""",
                           (line_name))
            for r in cursor:
                stations.append(r[0])
                operators.append(r[1])
        except MySQLdb.Error, e:
            print "Error %d: %s" % (e.args[0], e.args[1])
            
    print "done!"
    return tr.Line(name=line_name,
                   stations=stations,
                   operators=operators)

def load_missions(line, connection):
    """Return list of Mission objects base on database."""
    
    print "Loading missions...",
    missions = []

    with closing(connection.cursor()) as cursor:
        try:
            cursor.execute("""SELECT name, direction
            FROM missions
            WHERE line=%s;""",
            (line.name))
            missions_names = []
            directions = []
            for r in cursor:
                missions_names.append(r[0])
                directions.append(r[1])

            for i in xrange(len(missions_names)):
                cursor.execute("""
                SELECT s.name, md.time
                FROM stations as s, missions as m, missions_description as md
                WHERE m.name=%s AND m.id=md.mission_id AND s.id=md.station_id;""",
                (missions_names[i]))
                stations = []
                times = []
                for r in cursor:
                    stations.append(r[0])
                    times.append(r[1])
                missions.append(tr.Mission(missions_names[i],
                    line,
                    stations,
                    times,
                    directions[i]))
        except MySQLdb.Error, e:
            print "Error %d: %s" % (e.args[0], e.args[1])

    print "done!"
    return missions

def match_mission(mission_name, missions):
    """Return Mission corresponding to name."""

    match = None
    ind = 0
    while match is None and ind < len(missions):
        if missions[ind].name == mission_name:
           match = missions[ind]
        ind += 1
    return match

def collect_unidentified_trains(missions, connection):
    """Return remaining unidentified trains."""

    print "Collecting trains..."
    res = []
    with closing(connection.cursor()) as cursor:
        try:
            cursor.execute("""SELECT
                           c.mission, c.departure_time, sm.db, c.mission_id, c.id
                           FROM
                           capture as c, stations_matching as sm
                           WHERE
                           c.train_id IS NULL
                           AND c.station = sm.web
                           AND c.departure_time > %s
                           ORDER BY c.departure_time;""",
                           (START_DATE))

            for r in cursor:
                m_id = None
                if r[3] > 0:
                    m_id = r[3]
                m = match_mission(r[0], missions)
                if m is None:
                    cursor.execute("""UPDATE capture
                    SET train_id=-1
                    WHERE id=%s;""",
                    (r[4]))
                else:
                    res.append(tr.Status(time=r[1],
                        mission=m,
                        station=r[2].replace('-', ' ').lower(),
                        mission_id=m_id,
                        source='theoric'))

        except MySQLdb.Error, e:
            print "Error %d: %s" % (e.args[0], e.args[1])

    print "Collected"
    return res

def get_historic(unid_trains, missions, connection):
    """Return previously identified trains in order to chain."""

    print "Getting historic"
    times = [s.time for s in unid_trains]
    oldest_time = sorted(times)[0]

    res_trains = []
    with closing(connection.cursor()) as cursor:
        try:
            cursor.execute("""SELECT
            c.mission, c.departure_time, sm.db, c.mission_id, c.train_id
            FROM
            capture as c, stations_matching as sm
            WHERE
            c.train_id <> -1
            AND c.station = sm.web
            AND TIMESTAMPDIFF(SECOND, %s, c.departure_time) < %s
            AND c.departure_time > %s;""",
            (oldest_time, HISTORIC_LENGTH, START_DATE))

            remaining_trains = []
            for c in cursor:
                remaining_trains.append(c)
            while len(remaining_trains) > 0:
                r = remaining_trains[0]
                m = match_mission(r[0], missions)
                if m is not None:
                    m_id = None
                    if r[3] > 0:
                        m_id = r[3]
                    hist = [(t[1], t[2]) for t in remaining_trains
                            if t[4] == r[4]]
                    hist_pos = [(h[0], m.get_station_position(h[1]))
                            for h in hist]
                    hist_clean = {h[1] : h[0] for h in hist_pos if h[1] != -1}
                    if len(hist_clean) == 0:
                        pdb.set_trace()
                    hist_sorted = []
                    for i in xrange(m.get_length()):
                        if i in hist_clean.keys():
                            hist_sorted.append(hist_clean[i])
                        else:
                            hist_sorted.append(0)
                    res_trains.append(tr.Train(train_id=r[4],
                                               historic=hist_sorted,
                                               mission=m,
                                               position=max(hist_clean.keys()),
                                               mission_id=m_id))

                    remaining_trains = [t for t in remaining_trains
                            if t[4] != r[4]]
                else:
                    remaining_trains = [t for t in remaining_trains
                            if t[0] != r[0]]

        except MySQLdb.Error, e:
            print "Error %d: %s" % (e.args[0], e.args[1])

    print "Got it"
    return res_trains

def append_new_trains(status, trains, connection):
    """Append new elements to current trains."""

    print "Appending new trains"
    with closing(connection.cursor()) as cursor:
        try:
            cursor.execute("""SELECT MAX(train_id)
            FROM capture;""")
            #TODO: trouver une maniere propre de recup cursor[0]
            for c in cursor:
                cur_id = c[0]
            if cur_id is None:
                cur_id = 0
            next_id = cur_id + 1
        except MySQLdb.Error, e:
            print "Error %d: %s" % (e.args[0], e.args[1])

    ordered_status = sorted(status, key=lambda s: s.time)
    for s in ordered_status:
        next_id = ch.add_row(s, trains, next_id)
    print "Appended"

def update_database(trains, connection):
    """Update database with new information."""

    print "Upating database"
    try:
        for t in trains:
            query = ''
            with closing(connection.cursor()) as cursor:
                hist = t.get_valid_stations()
                for st, ti in hist.iteritems():
                    cursor.execute("""SELECT c.id
                    FROM capture AS c, stations_matching AS sm
                    WHERE c.station = sm.web AND c.train_id IS NOT NULL AND c.train_id=%s AND sm.db LIKE %s;""",
                    (t.train_id, "%" + st + "%"))
                    #TODO: trouver un moyen propre de check cursor
                    cs = []
                    for c in cursor:
                        cs.append(c)
                    if len(cs) == 0:
                        query += """UPDATE capture as c, stations_matching as sm
                                SET c.train_id={0}
                                WHERE c.departure_time='{1}'
                                AND c.station = sm.web
                                AND sm.db LIKE "%{2}%";""".format(t.train_id, ti.strftime('%Y-%m-%d %H:%M:%S'), st)
            if len(query) > 0:
                with closing(connection.cursor()) as cursor:
                    cursor.execute(query)
    except MySQLdb.Error, e:
        print "Error %d: %s" % (e.args[0], e.args[1])
    print "Updated"

def mission_to_png(trains, mission_name, file_name):
    sub_trains = []
    ids = []
    for t in trains:
        if t.get_mission().name == mission_name:
            sub_trains.append(t)
            ids.append(t.train_id)

    for t in trains:
        if t.train_id in ids and t not in sub_trains:
            sub_trains.append(t)

    if len(sub_trains) > 0:
        pic = gt.GraphicTrain(sub_trains)
        pic.save(file_name)
        return True

    return False


connection = MySQLdb.connect(user=DB_USER,
        passwd=DB_PWD,
        db=DB_NAME,
        host=DB_HOST,
        charset="utf8",
        use_unicode=True)
connection.autocommit(True)

line = load_line(LINE_NAME, connection)
missions = load_missions(line, connection)

unid_trains = collect_unidentified_trains(missions, connection)
if len(unid_trains) > 0:
    trains = get_historic(unid_trains, missions, connection)
    append_new_trains(unid_trains, trains, connection)
    update_database(trains, connection)
