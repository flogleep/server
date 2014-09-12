"""Script importing missions from file."""

import xlrd
import pickle
import train_objects as tr

wb = xlrd.open_workbook('../data/clean/missions_east_zz.xls')
sh = wb.sheet_by_name(wb.sheet_names()[0])

f = open('./rer_a_v2.p', 'rb')
rer_a = pickle.load(f)
f.close()

missions = []
stat_col = sh.col_values(0)
for colnum in xrange(1, sh.ncols):
    c = sh.col_values(colnum)

    m_name = c[0]
    t = 0
    stations = []
    times = []
    for i in xrange(1, len(c)):
        if c[i] != '':
            stations.append(stat_col[i])
            times.append(t)
            t += 3
    missions.append(tr.Mission(m_name, rer_a, stations, times, 1))

f = open('rer-a_east_missions_zz.p', 'wb')
pickle.dump(missions, f)
f.close()
