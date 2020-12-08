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


