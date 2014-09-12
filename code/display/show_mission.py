"""Module for drawing graphical results."""

import graphic_train as gt


def mission_to_png(mission_name, file_name):
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
