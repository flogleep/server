import string
import pdb
import train_objects as tr
import pygame as pg
from pygame.locals import *
import sys
from datetime import time
import datetime


HEADER_HEIGHT = 30
FIRST_COL_WIDTH = 170
STATION_HEIGHT = 30
STATION_WIDTH = 65
LINE_WIDTH = 9
CIRCLE_RAD = 12
LIGHT_COLOR = (255, 255, 255)
DARK_COLOR = (255, 255, 220)


class GraphicTrain(object):

    """Class for ploting trains."""

    def __init__(self, trains, primary_color=pg.Color(255, 100, 100), \
                 secondary_color=pg.Color(100, 100, 255)):
        self.trains = trains
        self.mission = self.trains[0].get_mission()
        self.update_station_list()
        self.nb_stations = len(self.station_list)
        self.primary_color = primary_color
        self.secondary_color = secondary_color

        height = HEADER_HEIGHT + self.nb_stations * STATION_HEIGHT
        width = FIRST_COL_WIDTH + STATION_WIDTH * 25

        pg.init()
        self.window = pg.Surface((width, height))
        #pg.display.set_caption(self.trains[0].get_mission().name)
        self.window.fill(pg.Color(255, 255, 255))

        self.never_updated = True
        self.font = pg.font.SysFont(None, 20)
        self.update_station_list()

    def update_station_list(self):
        """Update the station list so it contains all served stations."""
        #TODO: Do something with Line to make things easier

        sl = []
        for s in self.mission.stations:
            sl.append(string.replace(string.replace(s, "-", " ").lower(), "saint", "st"))
            if sl[-1] == 'grande arche la defense':
                sl[-1] = 'la defense (grande arche)'
        self.station_list = sl

        #sl = []
        #for s in self.mission.line.stations[11:35]:
        #    sl.append(string.replace(string.replace(s, "-", " ").lower(), "saint", "st"))

        ##sl[8] = 'la defense (grande arche)'
        #self.station_list = sl

        #sl = self.mission.get_station_list()
        #for t in self.trains:
        #    if not t.get_mission().is_similar(self.mission):
        #        new_sl = t.get_mission().get_station_list()
        #        i = 0
        #        while i < len(new_sl):
        #            if new_sl[i] not in sl:
        #                if i > 0:
        #                    sl.insert(sl.index(new_sl[i - 1]) + 1, new_sl[i])
        #                    i += 1
        #                else:
        #                    while new_sl[i] not in sl:
        #                        i += 1
        #                    ind = sl.index(new_sl[i])
        #                    k = i
        #                    while k > 0:
        #                        k -= 1
        #                        sl.insert(ind, new_sl[k])
        #            else:
        #                i += 1

        #self.station_list = sl

    def sort_trains(self):
        """Sort trains from oldest to newest."""

        id_list = []
        train_list = []
        for t in self.trains:
            if len(id_list) == 0:
                id_list.append(t.get_id())
                train_list.append([t])
            elif t.get_id() in id_list:
                ind = id_list.index(t.get_id())
                train_list[ind].append(t)
            else:
                ind = 0
                while ind < len(id_list) and t.get_id() < id_list[ind]:
                    ind += 1
                id_list.insert(ind, t.get_id())
                train_list.insert(ind, [t])
                #i = 0
                #prev_inc = 1
                #inc = 1
                #while i >= 0 and i < len(id_list) and inc <= prev_inc:
                #    j = 0
                #    prev_inc = inc
                #    inc = 0
                #    while inc == 0 and j < len(train_list[i]):
                #        inc = t.is_ahead(train_list[i][j])
                #        j += 1
                #    i += inc
                #i = max(i, 0)
                #id_list.insert(i, t.get_id())
                #train_list.insert(i, [t])

        self.id_list = id_list
        self.train_list = train_list

    def get_row(self, station):
        """Get row corresponding to a station."""

        form_s = string.replace(station, "-", " ").lower()
        form_s = form_s.replace("saint", "st")
        return self.station_list.index(form_s)

    def get_column(self, train):
        """Get column corresponding to a given train."""

        return self.id_list.index(train.get_id()) + 1

    def cell(self, row, col):
        """Return coordinates associated to row & col."""

        if row == -1:
            row_coord = int(HEADER_HEIGHT * .5)
        else:
            row_coord = int(HEADER_HEIGHT + STATION_HEIGHT * (row + .5))

        if col == 0:
            col_coord = int(FIRST_COL_WIDTH * .5)
        else:
            col_coord = int(FIRST_COL_WIDTH + STATION_WIDTH * (col - .5))

        return (col_coord, row_coord)

    def draw_line(self, cell1, cell2, color):
        """Draw line from cell1 to cell2."""

        pg.draw.line(self.window, \
                     color, \
                     self.cell(*cell1), \
                     self.cell(*cell2), \
                     LINE_WIDTH)

    def draw_circle(self, cell, color):
        """Draw a circle in the corresponding cell."""

        pg.draw.circle(self.window, \
                       color, \
                       self.cell(*cell), \
                       CIRCLE_RAD)

    def draw_empty_circle(self, cell, color):
        """Draw an empty circle in the corresponding cell."""

        pg.draw.circle(self.window, \
                       color, \
                       self.cell(*cell), \
                       CIRCLE_RAD)
        pg.draw.circle(self.window, \
                       pg.Color(255, 255, 255), \
                       self.cell(*cell), \
                       CIRCLE_RAD - 4)

    def add_text(self, cell, text):
        """Add a text to a cell."""

        label = self.font.render(text, 1, (0, 0, 0))
        labelpos = label.get_rect()
        cellxy = self.cell(*cell)
        labelpos.centerx = cellxy[0]
        labelpos.centery = cellxy[1]
        self.window.blit(label, labelpos)

    def add_subtext(self, cell, text):
        """Add a subtext to a cell."""

        label = self.font.render(text, 1, self.secondary_color)
        labelpos = label.get_rect()
        cellxy = self.cell(*cell)
        labelpos.centerx = cellxy[0] + int(.3 * STATION_WIDTH)
        labelpos.centery = cellxy[1] + int(.3 * STATION_HEIGHT)
        self.window.blit(label, labelpos)

    def update(self):
        """Update the drawings."""

        self.window.fill(pg.Color(255, 255, 255))

        self.update_station_list()
        self.sort_trains()

        for i in xrange(len(self.station_list)):
            if i % 2 == 0:
                color = LIGHT_COLOR
            else:
                color = DARK_COLOR
            rect = pg.Rect(0, i * STATION_HEIGHT, 10000, STATION_HEIGHT)
            pg.draw.rect(self.window, color, rect)

        self.draw_line((0, 0), (len(self.station_list) - 1, 0), self.primary_color)
        for i in xrange(len(self.station_list)):
            self.draw_circle((i, 0), self.primary_color)
            self.add_text((i, 0), self.station_list[i])

        for t in self.trains:
            if t.is_zz():
                color = self.secondary_color
            else:
                color = self.primary_color

            column = self.get_column(t)
            first_row = self.get_row(t.get_first_station())
            last_row = self.get_row(t.get_last_station())
            
            self.add_text((-1, column), t.last_update().strftime('%m-%d'))
            self.draw_line((first_row, column), (last_row, column), color)
            delay = 0
            for i in xrange(len(t.historic)):
                if t.historic[i] != 0 or t.ghost[i] != 0:
                    r = self.get_row(t.get_mission().get_station(i))
                    if t.historic[i] == 0:
                        self.draw_empty_circle((r, column), color)
                    else:
                        self.draw_circle((r, column), color)
                        strtime = "{0}".format(
                                t.historic[i].strftime('%H:%M:%S'))
                        self.add_text((r, column), strtime)
                        k_max = -1
                        if i > 0:
                            for k in xrange(i):
                                if t.historic[k] != 0:
                                    k_max = k
                        if k_max > -1:
                            t_prev = t.historic[k_max]
                            t_cur = t.historic[i]
                            #time_second = 3600 * t_cur.hour + 60 * t_cur.minute + t_cur.second \
                            #        - 3600 * t_prev.hour - 60 * t_prev.minute - t_prev.second
                            time_second = (t_cur - t_prev).total_seconds()
                            theo = self.mission.theoretical_time(self.mission.get_station(k_max), \
                                                                self.mission.get_station(i))
                            theo_second = theo
                            diff_second = time_second - theo_second
                            delay += diff_second
                            self.add_subtext((r, column), str(int(delay)))

    def show(self):
        """Display the trains."""
        self.update()

        while True:
            for e in pg.event.get():
                if e.type == QUIT:
                    pg.display.quit()
                    return 0
                elif e.type == pg.KEYDOWN:
                    keys = pg.key.get_pressed()
                    if keys[K_LEFT]:
                        return -1
                    elif keys[K_RIGHT]:
                        return 1
                    elif keys[K_DOWN]:
                        return 2
                    elif keys[K_UP]:
                        return -2
            pg.display.update()

    def save(self, fname):
        """Save current display."""

        self.update()
        pg.image.save(self.window, fname)


#test_mission = tr.Mission('TEST', 0, ['Stat1', 'Stat2', 'Stat3'], [0, 1, 3], ['Stat3'])
#test_train1 = tr.Train(test_mission, 1, [1, 2, 0])
#test_train2 = tr.Train(test_mission, 0, [3, 0, 0])
#trains = [test_train1, test_train2]
#test = GraphicTrain(trains)
#test.show()
