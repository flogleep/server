import train_objects as tr
import graphic_train as gt
import MySQLdb
import sys
import pickle
from contextlib import closing
import pdb

DB_USER = 'root'
DB_PWD = ''
DB_HOST = 'localhost'
DB_NAME = 'rer'

def load_missions(line, connection):
    """Return list of Mission objects base on database."""

    missions = []

    with closing(connection.cursor()) as cursor:
        try:
            print "Loading missions..."
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

    print "Loaded"
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

def get_historic(mission, connection):
    """Return previously identified trains in order to chain."""

    print "Getting historic"

    res_trains = []
    with closing(connection.cursor()) as cursor:
        try:
            cursor.execute("""SELECT
            c.mission, c.departure_time, sm.db, c.mission_id, c.train_id
            FROM
            capture as c, stations_matching as sm
            WHERE
            c.train_id <> -1
            AND c.mission = %s
            AND c.station = sm.web;""",
            (mission.name))

            remaining_trains = []
            for c in cursor:
                remaining_trains.append(c)
            while len(remaining_trains) > 0:
                r = remaining_trains[0]
                m_id = None
                if r[3] > 0:
	                m_id = r[3]
                hist = [(t[1], t[2]) for t in remaining_trains
                	   if t[4] == r[4]]
                hist_pos = [(h[0], mission.get_station_position(h[1]))
			                for h in hist]
                hist_clean = {h[1] : h[0] for h in hist_pos if h[1] != -1}
                hist_sorted = []
                for i in xrange(mission.get_length()):
                	if i in hist_clean.keys():
                	   hist_sorted.append(hist_clean[i])
                	else:
                            hist_sorted.append(0)
                res_trains.append(tr.Train(train_id=r[4],
                                           historic=hist_sorted,
                                           mission=mission,
                                           position=max(hist_clean.keys()),
                                           mission_id=m_id))

                remaining_trains = [t for t in remaining_trains
                                    if t[4] != r[4]]

        except MySQLdb.Error, e:
            print "Error %d: %s" % (e.args[0], e.args[1])

    return res_trains

def mission_to_png(trains, file_name):
    pic = gt.GraphicTrain(trains)
    pic.save(file_name)

    return True

if __name__ == '__main__':
    if len(sys.argv) == 1:
        print "Need at least one argument (mission name)"
    else:
        connection = MySQLdb.connect(user=DB_USER,
                                     passwd=DB_PWD,
                                     db=DB_NAME,
                                     host=DB_HOST,
                                     charset="utf8",
                                     use_unicode=True)
        connection.autocommit(True)

        line = pickle.load(open('./rer-a.p', 'rb'))
        line.name = 'A'
        missions = load_missions(line, connection)
        mission = match_mission(sys.argv[1], missions)

        trains = get_historic(mission, connection)
        ROOT_DIR = './'
        f_name = ROOT_DIR + mission.name + '.png'
        mission_to_png(trains, f_name)