"""Trains and missions modelization."""

import pdb
import nltk


def is_number(x):
    """Return True if x is a number."""
    try:
        x + 1
        return True
    except TypeError:
        return False


class Line(object):

    """
    Train or subway line.

    name     | string       | Name of the line.
    stations | list<string> | List of stations served by the line

    """

    def __init__(self, name, stations, letters=None, branchs=None, operators=None):
        self.name     = name
        self.stations = stations
        self.letters  = letters
        self.branchs  = branchs
        self.operators = operators

    def get_stations(self):
        """Return the list of stations names."""

        return self.stations.keys()

    def get_path(self, departure, arrival):
        """Return the list of stations corresponding to a path."""
        #TODO: think about a more clever way of doing that

        b_indexes_d = []
        b_indexes_a = []
        for i in xrange(len(self.branchs)):
            if departure in self.branchs[i]:
                b_indexes_d.append(i)
            if arrival in self.branchs[i]:
                b_indexes_a.append(i)

        if len(b_indexes_d) > 1:
            if len(b_indexes_a) > 1:
                b_index_d = 0
                b_index_a = 0
            else:
                b_index_a = b_indexes_a[0]
                if b_index_a in b_indexes_d:
                    b_index_d = b_index_a
                else:
                    b_index_d = 0
        elif len(b_indexes_a) > 1:
            b_index_d = b_indexes_d[0]
            if b_index_d in b_indexes_a:
                b_index_a = b_index_d
            else:
                b_index_a = 0
        else:
            b_index_d = b_indexes_d[0]
            b_index_a = b_indexes_a[0]

        s_index_d = self.branchs[b_index_d].index(departure)
        s_index_a = self.branchs[b_index_a].index(arrival)

        path = []
        if b_index_a == b_index_d:
            if s_index_d < s_index_a:
                path += self.branchs[b_index_d][s_index_d:s_index_a]
            else:
                path += self.branchs[b_index_d][s_index_d:s_index_a:-1]
        else:
            if b_index_d > 0:
                path += self.branchs[b_index_d][s_index_d::-1]
                if b_index_a > 0:
                    if path[-1] == self.branchs[0][0]:
                        path += self.branchs[0][1:]
                    else:
                        path += self.branchs[0][-2::-1]
                    path += self.branchs[b_index_a][1:s_index_a]
                else:
                    if path[-1] == self.branchs[0][0]:
                        path += self.branchs[0][1:s_index_a]
                    else:
                        path += self.branchs[0][-2:s_index_a:-1]
            else:
                if self.branchs[0][0] == self.branchs[b_index_a][0]:
                    path += self.branchs[0][s_index_d::-1]
                else:
                    path += self.branchs[0][s_index_d:]
                path += self.branchs[b_index_a][1:s_index_a]

        path.append(arrival)
        return path

    def station_from_letter(self, letter):
        """Return station corresponding to letter."""

        return '_'
        return self.letters[letter]

    def get_operator (self, station_name):
        """Return the operator associated to a given station."""

        return self.operators[self.stations.index(station_name)]
        


class Mission(object):

    """
    Train mission on a specific line.

    name      | string       | Short name of the mission
    line      | Line         | Line over which the mission applies
    stations  | list<string> | Stations served by the mission
    times     | list<double> | Minutes between stations
    direction | {-1, 1}      | Mission direction
    name_aux  | string       | Complement of the mission name
    full_name | string       | Complete name of the mission

    """

    def __init__(self, name, line, stations, times, direction, name_aux='', \
            frequency=0):
        self.name      = name
        self.line      = line
        self.stations  = stations
        self.times     = times
        self.direction = direction
        self.name_aux  = name_aux
        self.frequency = frequency

    def update_station_list(self):
        """Change some stations names."""

        for i in xrange(len(self.stations)):
            if 'grande arche' in self.stations[i].lower():
                self.stations[i] = 'la defense (grande arche)'


    def update_times(self):
        """Complete missing values in times."""

        for i in xrange(len(self.times)):
            if not is_number(self.times[i]):
                if i == 0:
                    self.times[0] = self.times[1] - 2
                elif i == len(self.times) - 1:
                    self.times[-1] = self.times[-2] + 2
                else:
                    if is_number(self.times[i + 1]):
                        self.times[i] = .5 * self.times[i - 1] + self.times[i + 1]
                    else:
                        self.times[i] = self.times[i - 1] + 2

    def get_direction(self):
        """Return mission direction on the Line."""

        return self.direction

    def get_full_name(self):
        """Return mission full name."""

        return self.name

    def get_frequency(self):
        """Return mission frequency."""

        return self.frequency

    def first_station(self):
        """Return mission first station."""

        return self.stations[0]

    def is_zz(self):
        """Return whether or not current mission is a ZZ mission."""

        return self.name[2:] == "ZZ"

    def is_similar(self, m):
        """Return true if two missions have same name."""

        return self.get_full_name() == m.get_full_name()

    def is_admissible(self, m):
        """Return true if a m is a ZZ version of current mission."""

        return self.line.station_from_letter(m.name[2]) == self.first_station() \
                and m.is_zz()

    def get_station_position(self, station):
        """Return the station position in the mission."""

        if station in self.get_station_list():
            return self.stations.index(station)
        else:
            sts = self.get_station_list()
            min_dist = nltk.metrics.edit_distance(station, sts[0])
            ind_min_dist = 0
            for i in xrange(1, len(sts)):
                m = nltk.metrics.edit_distance(station, sts[i])
                if m < min_dist:
                    min_dist = m
                    ind_min_dist = i
            return ind_min_dist


    def get_length(self):
        """Return the number of stations served."""

        return len(self.stations)

    def get_station(self, position):
        """Return the station at the given position."""

        return self.stations[position]

    def get_station_list(self):
        """Return the list of stations served by mission."""

        return self.stations

    def theoretical_time(self, station1, station2):
        """Return the theoretical travel time between two stations."""

        ind1 = self.get_station_position(station1)
        ind2 = self.get_station_position(station2)
        #TODO: corriger ce bug et check robustesse
        #if (type(self.times[ind1]) is not float\
        #        and type(self.times[ind1]) is not int)\
        #        or (type(self.times[ind2]) is not float\
        #        and type(self.times[ind2]) is not int):
        #    pdb.set_trace()
        #    return 2 * 60
        #else:
        i_t1 = int(60 * self.times[ind1])
        i_t2 = int(60 * self.times[ind2])

        if i_t1 > i_t2:
            t = i_t2
            i_t2 = i_t1
            i_t1 = t

        return i_t2 - i_t1

    def has_operator_changed (self, station1, station2):
        """Return whether or not the operator changes between two positions."""

        operator1 = self.line.get_operator(station1)
        operator2 = self.line.get_operator(station2)

        return operator1 != operator2
        

class Train(object):

    """
    Train executing a specific mission.

    mission  | Mission         | Mission the train is executing
    position | int             | Train position on its mission
    historic | list<timestamp> | Reaching time of each stations

    """

    def __init__(self, train_id, mission, position, mission_id=None, historic=None, pos_time=None):
        self.train_id = train_id
        self.mission  = mission
        self.position = position
        self.mission_id = mission_id
        self.active   = True
        self.ghosted  = False

        if historic is None:
            self.historic = [0] * self.mission.get_length()
        else:
            self.historic = historic

        if not pos_time is None:
            self.historic[position] = pos_time

        self.ghost = [0] * self.mission.get_length()

    def get_direction(self):
        """Return train's direction on the Line."""

        return self.get_mission().get_direction()

    def get_mission_id (self):
        """Return train's mission id."""

        return self.mission_id
                
    def get_id(self):
        """Return train's id."""

        return self.train_id

    def set_id(self, new_id):
        """Change train's id."""

        self.train_id = new_id

    def set_same_id(self, t):
        """Set current train's id to t's id."""

        self.set_id(t.get_id())
        t.active = False

    def get_mission(self):
        """Return train's mission."""

        return self.mission

    def get_mission_full_name(self):
        """Return train's full mission name."""

        return self.mission.get_full_name() + str(self.mission_id)

    def get_station(self, formatted=False):
        """Return train's current station."""

        station = self.get_mission().get_station(self.position)
        if formatted:
            return station.lower().replace("-", " ")
        else:
            return station

    def get_position(self):
        """Return train's position index."""

        return self.position

    def last_ghost(self):
        """Return train's last position."""

        ind = self.get_position()
        for i in range(self.get_mission().get_length() - 1, ind, -1):
            if self.ghost[i] != 0:
                return i

        return ind

    def is_zz(self):
        """Return whether or not current train is omnibus."""

        return self.get_mission().is_zz()

    def get_time(self, position, seconds=True):
        if self.historic[position] == 0:
            return self.ghost[position]
        else:
            if seconds:
                return self.historic[position].second \
                    + 60 * self.historic[position].minute \
                    + 3600 * self.historic[position].hour
            else:
                return self.historic[position]

    def get_station_time(self, station_name, seconds=True):
        """Return time associated to the station."""

        return self.get_time(self.get_mission().get_station_position(station_name), seconds)

    def get_current_operator (self):
        """Return current operator."""

        return self.mission.line.get_operator(self.get_station())
        
    
    def is_ahead(self, t):
        """Return -1, 0 or 1 whether the current train is behind or ahead of t."""
        #TODO: nettoyer
        #TODO: rendre robuste dans le cas ou la mission est differente

        if self.get_position() > t.get_position():
            if self.get_time(t.get_position(), seconds=False) != 0:
                if self.get_time(t.get_position(), seconds=False) < t.last_update():
                    return 1
                else:
                    return -1
            return 1
        elif self.get_position() < t.get_position():
            if t.get_time(self.get_position(), seconds=False) != 0:
                if t.get_time(self.get_position(), seconds=False) == 68549:
                    pdb.set_trace()
                if t.get_time(self.get_position(), seconds=False) < self.last_update():
                    return -1
                else:
                    return 1
            return -1
        else:
            if self.last_update() < t.last_update():
                return 1
            else:
                return -1

    def is_admissible(self, status):
        """Return whether or not the train is admissible """

        return True

    def get_station_list(self):
        """Return the stations list of the mission."""

        return self.get_mission().get_station_list()

    def last_update(self, seconds=False):
        """Return the last update time."""

        if self.historic[self.position] == 0:
            return 0
        if seconds:
            return self.historic[self.position].second \
                    + 60 * self.historic[self.position].minute \
                    + 3600 * self.historic[self.position].hour

        return self.historic[self.position]

    def get_first_station(self):
        """Return the name of the oldest station."""

        pos = 0
        found = False
        while pos < len(self.historic) and not found:
            found = self.historic[pos] != 0
            pos += 1
        pos -= 1

        if pos == len(self.historic):
            return None
        else:
            return self.get_mission().get_station(pos)

    def get_last_station(self):
        """Return the name of the latest station."""

        pos = len(self.historic) - 1
        found = False
        while pos >= 0 and not found:
            found = self.historic[pos] != 0
            pos -= 1
        pos += 1

        if pos < 0:
            return None
        else:
            return self.get_mission().get_station(pos)

    def update_from_status(self, row):
        """Update the train's position based on a Status update."""

        #if self.historic[row.get_position()] != 0:
        if False:
            if row.get_time() < self.historic[row.get_position()]:
                pdb.set_trace()
            if row.get_time() < self.last_update():
                pdb.set_trace()
            if row.get_position() < self.get_position():
                pdb.set_trace()
        self.mission_id = row.mission_id
        self.update_position(row.get_position(), row.get_time())

    def update_position(self, new_position, time):
        """Update the train's current position."""

        if new_position >= len(self.historic):
            pass
        else:
            self.position = new_position
            self.historic[self.position] = time
            self.ghosted = False

    def show(self):
        """Nice print method."""

        print "Train mission: {0}".format(self.get_mission_full_name())
        print "Train position: {0}".format(self.get_station())
        print "Historic :"
        for i in xrange(len(self.historic)):
            print "\t{0}: {1}".format(self.mission.get_station(i), self.historic[i])

    def get_valid_stations(self):
        res = {}
        for i in xrange(len(self.historic)):
            if self.historic[i] != 0:
                res[self.get_station_list()[i]] = self.historic[i]
        return res


class Status(object):

    """
    Status of a station at a given time.

    time    | timestamp            | Ping time
    mission | Mission              | Full mission name
    station | string               | Station name
    status  | string               | Train status at the station
    source  | {web, user, theoric} | Status source

    """

    def __init__(self, time, mission, station, status='',
            mission_id=None, source='theoric'):
        if station in mission.get_station_list():
            self.station = station
        else:
            sts = mission.get_station_list()
            min_dist = nltk.metrics.edit_distance(station, sts[0])
            ind_min_dist = 0
            for i in xrange(1, len(sts)):
                m = nltk.metrics.edit_distance(station, sts[i])
                if m < min_dist:
                    min_dist = m
                    ind_min_dist = i

            self.station = sts[ind_min_dist]

        self.time    = time
        self.mission = mission
        self.status  = status
        self.source  = source
        self.mission_id = mission_id

    def get_mission(self):
        """Return train's mission."""

        return self.mission

    def get_mission_full_name(self):
        """Return train's full mission name."""

        return self.mission.get_full_name() + str(self.mission_id)

    def get_mission_id (self):
        """Return mission id."""

        return self.mission_id        

    def get_time(self, seconds=False):
        """Return status ping time."""

        if seconds:
            return self.time.second + 60 * self.time.minute + 3600 * self.time.hour

        return self.time

    def get_station(self, formatted=False):
        """Return train current station."""

        if formatted:
            return self.station.lower().replace("-", " ")
        else:
            return self.station

    def get_position(self):
        """Return the station position in the mission."""

        return self.mission.get_station_position(self.station)

