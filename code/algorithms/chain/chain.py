"""Dirty module for testing algorithm idea."""

import train_objects as tr
import graphic_train as gt
import pdb
import pickle
from datetime import time, timedelta, datetime
import os


LOW_THRESHOLD = .2
LOW_FREQ_THRESHOLD = .5
HIGH_THRESHOLD = 30 * 60
ID_THRESHOLD = 20 * 60
GHOST_THRESHOLD = 600
DOUBLON_THRESHOLD = 0 * 60

WHITE_LIST = ['fecture', 'fense', 'vincennes', 'fontenay', 'noisy', 'nation', 'gaulle', 'neuilly', 'sartrouville', 'houilles']

def is_possible_time(station1, time1, station2, time2, mission):
    """Return whether or not a travel time is possible."""

    if time1 == 0 or time2 == 0:
        return False

    theoretical_time = mission.theoretical_time(station1, station2)
    effective_time = (time2 - time1).total_seconds()
    possible_time = effective_time > LOW_THRESHOLD * (theoretical_time - 60)
    possible_time = possible_time and effective_time < theoretical_time + HIGH_THRESHOLD

    return possible_time

def is_possible(train, row, v=False, use_id=True):
    """Return whether or not a train is compatible with a status."""

    if not train.active:
        if v:
            print "inactive"
        return False

    same_mission = train.get_mission().is_similar(row.get_mission())
    if not same_mission:
        if v:
            print "other mission"
        return False

    if row.get_mission_id() is not None and use_id:
        if (train.last_update() - row.get_time()).total_seconds() > ID_THRESHOLD:
            return False
        if row.mission.has_operator_changed(row.get_station(), train.get_station()):
            if train.get_position() > row.get_position():
                return False
                
            return is_possible_time(train.get_station(),
                                    train.last_update(),
                                    row.get_station(),
                                    row.get_time(),
                                    train.get_mission())

        return train.get_mission_id() == row.get_mission_id()\
            and (train.last_update() - row.get_time()).total_seconds() < ID_THRESHOLD

    possible_position = train.get_position() < row.get_position()
    if not possible_position:
        if v:
            print "impossible position"
        return False

    ghosted = train.ghost[row.get_position()] != 0
    if ghosted:
        if v:
            print "ghosted"
        return False

    return is_possible_time(train.get_station(), train.last_update(), \
                            row.get_station(), row.get_time(), \
                            train.get_mission())

def get_best_match(train, all_trains):
    """Return the best possible match for a train that went ZZ."""

    zz_mission = train.get_mission()
    active_filter  = [t for t in all_trains if t.active]
    mission_filter = [t for t in active_filter if t.get_mission().is_admissible(zz_mission)]
    station_filter = []
    for t in mission_filter:
        if t.get_station() in zz_mission.get_station_list():
            if zz_mission.get_station_position(t.get_station()) < train.get_position():
                station_filter.append(t)
        else:
            i = t.get_position()
            while i < len(t.get_mission().get_station_list()) and t.get_mission().get_station(i) not in zz_mission.get_station_list():
                i += 1
            if i < len(t.get_mission().get_station_list()):
                station_filter.append(t)

    match = None
    for t in station_filter:
        if t.get_station() not in zz_mission.get_station_list() or \
           is_possible_time(t.get_station(), t.last_update(True), \
           train.get_station(), train.last_update(True), \
           zz_mission):
            if match is None:
                match = t
            else:
                if t.is_ahead(match) and is_possible_time(t.get_station(), \
                        t.last_update(True), train.get_station(), \
                        train.last_update(True), train.get_mission()):
                    match = t

    return match


def get_previous_train(row, all_trains):
    """
    Return the time between previous train and current train at the current
    train position.

    """

    prev_trains = [train for train in all_trains \
            if train.get_mission().is_similar(row.get_mission()) \
            and train.get_position() == row.get_position() \
            and train.last_update(True) < row.get_time(True)]
    if len(prev_trains) > 0:
        prev_trains.sort(lambda x, y: x.is_ahead(y))
        return prev_trains[-1]

    return None

def is_in_white_list(station):
    """Return whether or not a station is white-listed."""

    for s in WHITE_LIST:
        if s in station:
            return True
    return False

def update_ghost(current_trains, row):
    """Set unseen trains to ghosts."""

    for t in current_trains:
        if row.get_time(True) - t.last_update(True) > GHOST_THRESHOLD:
            t.ghosted = True

def add_row(row, current_trains, next_id, verbose=True):
    """Update train list with a new status row."""

    if verbose:
        print "{0} | {1:<30} |".format(row.get_time(), row.get_station()),

    doublons = [t for t in current_trains if t.get_station() == row.get_station()
                and t.get_mission() == row.get_mission()]
    for t in doublons:
        if (row.get_time() - t.last_update()).total_seconds() < DOUBLON_THRESHOLD:
            t.update_from_status(row)
            return next_id
    
    #Filtering trains with correct mission
    update_ghost([t for t in current_trains if is_possible(t, row)], row)
    mission_train = [t for t in current_trains if is_possible(t, row)
                     and not t.ghosted]

    if len(mission_train) == 0:
        t = tr.Train(None,
                     row.get_mission(),
                     row.get_position(),
                     pos_time=row.get_time(),
                     mission_id=row.mission_id)

        if t.get_mission().is_zz():
            m_t = get_best_match(t, current_trains)
            if m_t is None:
                print "New ZZ train created."
                t.set_id(next_id)
                current_trains.append(t)
                next_id += 1
            else:
                print "ZZ train linked to existing train."
                t.set_same_id(m_t)
                current_trains.append(t)
        else:
            prev_train = get_previous_train(row, current_trains)
            if prev_train is None:
                ghosts = [train for train in current_trains if is_possible(train, row)
                          and train.ghosted]
                if len(ghosts) == 0:
                    if row.get_position() == len(row.get_mission().get_station_list()) - 1:
                        print "Row skipped. Non relevant data."
                    else:
                        print "New train created. No previous train found"
                        t.set_id(next_id)
                        current_trains.append(t)
                        next_id += 1
                else:
                    print "Ghost found and reactivated."
                    ghosts.sort(lambda x, y: x.is_ahead(y))
                    updated_train = ghosts[-1]
                    updated_train.update_from_status(row)
                    #updated_train.update_position(row.get_position(), row.get_time())
            else:
                time_gap = t.last_update(True) - prev_train.get_time(row.get_position(), True)
                if time_gap < LOW_FREQ_THRESHOLD * row.get_mission().get_frequency():
                    if prev_train.get_position() != row.get_position():
                        print "Error: status incompatible with mission frequency information."
                    else:
                        print "Existing train found and overwritten."
                        prev_train.update_from_status(row)
                        #prev_train.update_position(row.get_position(), row.get_time())
                else:
                    ghosts = [train for train in current_trains if is_possible(train, row)
                              and train.ghosted]
                    if len(ghosts) == 0:
                        if row.get_position() == len(row.get_mission().get_station_list()) - 1:
                            print "Row skipped. Non relevant data."
                        else:
                            print "New train created. Time gap large enough : {0}s".format(time_gap)
                            t.set_id(next_id)
                            current_trains.append(t)
                            next_id += 1
                    else:
                        print "Ghost found and reactivated."
                        ghosts.sort(lambda x, y: x.is_ahead(y))
                        updated_train = ghosts[-1]
                        updated_train.update_from_status(row)
                        #updated_train.update_position(row.get_position(), row.get_time())


    else:
        #If there are matching trains, update the closest one
        print "Existing train found and updated."
        mission_train.sort(lambda x, y: x.is_ahead(y))
        if mission_train[0].get_position() == mission_train[-1].get_position():
            updated_train = mission_train[0]
        else:
            updated_train = mission_train[-1]
        prev_station = updated_train.get_station()
        current_station = row.get_station()
        all_prev_trains = [t for t in current_trains
                           if prev_station in t.get_mission().get_station_list()
                           and current_station in t.get_mission().get_station_list()
                           and t.get_time(t.get_mission().get_station_position(prev_station)) != 0
                           and t.get_time(t.get_mission().get_station_position(prev_station), seconds=False) <= updated_train.last_update()
                           and t.get_mission().direction == updated_train.get_mission().direction]
        updated_train_prev_pos = updated_train.get_station(True)
        updated_train.update_from_status(row)
        #updated_train.update_position(row.get_position(), row.get_time())
        if not is_in_white_list(updated_train_prev_pos):
            for t in all_prev_trains:
                if t != updated_train and not is_in_white_list(t.get_station(True)):
                    t.ghost[t.get_mission().get_station_position(current_station)] = updated_train.last_update()
                    if (max([d for d in t.ghost if d != 0]) - t.last_update()).total_seconds() > GHOST_THRESHOLD:
                        t.ghosted = True

    return next_id

def remove_row(row, current_trains, next_id):
    """Remove a row from the trains list."""

    for i in xrange(len(current_trains)):
        t = current_trains[i]
        if t.get_mission().is_similar(row.get_mission()) \
           and t.get_position() == row.get_position() \
           and t.historic[t.get_position()] == row.time:

            t.historic[t.get_position()] = 0
            j = 1

            while t.historic[-j] == 0 \
                and j < len(t.historic):
                j += 1
            if j < len(t.historic):
                t.position = len(t.historic) - j
            else:
                del current_trains[i]
    if len([1 for t in current_trains if t.get_id() == next_id - 1]) == 0:
        next_id -= 1
    return next_id

def import_input_data(missions, filename, sheet_name=None, first_row=1, \
                      time_col=0, mission_col=1, station_col=2, status_col=3,
                      mission_id_col=None):
    """Return list of Status corresponding to an input file."""

    wb = xlrd.open_workbook(filename)
    if sheet_name is None:
        sheet_name = wb.sheet_names()[0]
    sh = wb.sheet_by_name(sheet_name)
    st = []

    for rownum in xrange(first_row, sh.nrows):
        x_t = sh.row_values(rownum)[time_col]
        i_t = int(24 * 3600 * x_t)
        mission_name = sh.row_values(rownum)[mission_col]

        t       = time(i_t // 3600, (i_t % 3600) // 60, i_t % 60)
        station = sh.row_values(rownum)[station_col]
        status  = sh.row_values(rownum)[status_col]
        mission = next((m for m in missions \
                        if m.get_full_name() == mission_name), None)
        if sh.row_values(rownum)[mission_id_col] != '':
            mission_id = int(sh.row_values(rownum)[mission_id_col])
        else:
            mission_id = None

        if mission is not None:
            st.append(tr.Status(t, mission, station, status, mission_id))
        else:
            print "Unknown mission ({0}), row not imported".format(mission_name)

    return st
