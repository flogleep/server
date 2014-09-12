import xlrd
import pickle
import train_objects as tr

f = open('./rer_a.p', 'rb')
line = pickle.load(f)
f.close()
letters = {}
wb = xlrd.open_workbook('../data/clean/letter_station.xls')
sh = wb.sheet_by_name(wb.sheet_names()[0])
for rownum in xrange(sh.nrows):
    letters[sh.row_values(rownum)[0]] = sh.row_values(rownum)[1]
line_v2 = tr.Line(line.name, line.stations, letters)
f = open('./rer_a_v2.p', 'wb')
pickle.dump(line_v2, f)
f.close()
