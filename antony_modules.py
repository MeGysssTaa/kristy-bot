import datetime


def time_intervals(time_dict, default):
    """
    Модуль, который получает на вход dict времени в формате (start, end) : action,
    где start и end - это время начала и конца (формат ЧЧ:ММ),
    а action - это то, что должен вернуть модуль, если текущее время в этом интервале
    default - выводит, если временной промежуток не найдён
    return action or default
    """
    format_time = "%H:%M"
    zone = datetime.timedelta(hours=2)
    datetime_now = datetime.datetime.utcnow() + zone
    for interval in dict(time_dict).items():
        time_start = datetime.datetime.strptime(interval[0][0], format_time).time()
        time_end = datetime.datetime.strptime(interval[0][1], format_time).time()
        datetime_start = datetime.datetime.combine(datetime_now.date(), time_start)
        if time_start < time_end:
            datetime_end = datetime.datetime.combine(datetime_now.date(), time_end)
        else:
            datetime_end = datetime.datetime.combine(datetime_now.date() + datetime.timedelta(days=1), time_end)
        if datetime_start <= datetime_now < datetime_end:
            return interval[1]
    return default


def correct_shape(words, count):
    return words[0] if count % 10 == 1 and count != 11 else words[1] if 2 <= count % 10 <= 4 and not 12 <= count <= 14 else words[2]


def dictCorrect(dict_now):
    timed = {}
    for key, value in dict_now.items():
        if type(value) == dict:
            timed.update({key if not str(key).isdigit() else int(key): dictCorrect(value)})
        elif type(value) == list:
            timed.update({key if not str(key).isdigit() else int(key): listCorrect(value)})
        else:
            timed.update({key if not str(key).isdigit() else int(key): value})
    return timed


def listCorrect(list_now):
    timed = []
    for value in list_now:
        if type(value) == dict:
            timed.append(dictCorrect(value))
        elif type(value) == list:
            timed.append(listCorrect(value))
        else:
            timed.append(value)
    return timed
