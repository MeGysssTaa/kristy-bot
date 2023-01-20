from datetime import (
    datetime,
    timedelta
)

import timetable_parser


# Наибольшая продолжительность перерыва между парами в минутах.
MAX_BREAK_LEN_MINS = 30


def curtime(tt_data, chat):
    """
    Возвращает текущее время в часовом поясе, соответствующем указанной беседе.

    :param tt_data: Данные о расписаниях всех бесед (TimetableData).

    :param chat ID беседы, на часовой пояс которой необходимо ориентироваться.

    :return: объект datetime, соответствующий текущему времени для указанной беседы,
             или None, если данные для указанной беседы не были загружены.
    """
    tz = tt_data.timezones.get(chat, None)
    return None if tz is None else datetime.now(tz)


def weekday_ru(tt_data, chat):
    """
    Возвращает название текущего дня недели на русском языке ('Понедельник', 'Вторник', ...).

    :param tt_data: Данные о расписаниях всех бесед (TimetableData).

    :param chat: ID беседы, на часовой пояс которой необходимо ориентироваться.

    :return: строка, содержащая текущий день недели, которая может быть использована в функции get_class,
             или None, если данные для указанной беседы не были загружены.
    """
    now = curtime(tt_data, chat)
    return None if now is None else timetable_parser.WEEKDAYS_RU[now.weekday()]


def get_week(tt_data, chat):
    """
    Проверяет, верхняя (нечётная) или нижняя (чётная) ли сейчас неделя.

    :param tt_data: Данные о расписаниях всех бесед (TimetableData).

    :param chat ID беседы, на часовой пояс которой необходимо ориентироваться.

    :return: 'верхняя', если текущая неделя верхняя (нечётная),
             'нижняя', если текущая неделя нижняя (чётная),
             None, если данные для указанной беседы не были загружены.
    """
    now = curtime(tt_data, chat)

    if now is None:
        return None

    week_num = now.isocalendar()[1]
    return 'нижняя' if week_num % 2 == 1 else 'верхняя'


def is_cur_time_in_range(tt_data, chat, now, start_tstr, end_tstr):
    """
    Проверяет, находится ли текущее время в указанном временном диапазоне.

    :param tt_data: Данные о расписаниях всех бесед (TimetableData).

    :param now: Текущее время - datetime. Передаётся для того, чтобы не вычислять
                curtime() несколько раз за одну серию обращений.

    :param chat: ID беседы, на часовой пояс которой необходимо ориентироваться.

    :param start_tstr: Начало временного диапазона - str (например, '13.30').

    :param end_tstr: Конец временного диапазона - str (например, '21.05').

    :return: True, если текущее время находится в указанном временном диапазоне,
             False в противном случае. Если данные для указанной беседы не были
             загружены, возвращает None.
    """
    tz = tt_data.timezones.get(chat, None)

    if tz is None:  # если tz для этой беседы не определён, то и now для неё тоже неопределён => проверяем только tz
        return None

    start = tz.localize(now.combine(now.date(),
                                    datetime.strptime(start_tstr, timetable_parser.CLASS_TIME_FMT).time()))
    end = tz.localize(now.combine(now.date(),
                                  datetime.strptime(end_tstr, timetable_parser.CLASS_TIME_FMT).time()))

    return start <= now <= end


def class_ordinal(tt_data, chat, now):
    """
    Возвращает порядковый номер пары, которая проходит в указанный момент времени.

    :param tt_data: Данные о расписаниях всех бесед (TimetableData).

    :param chat: ID беседы, на часовой пояс которой необходимо ориентироваться.

    :param now: Момент времени, для которого нужно поставить в соответствие порядковый номер пары.
                Передаётся для того, чтобы можно было узнавать номер пары не только в текущий, а
                в любой момент времени. Например, это полезно, чтобы узнать, какая пара будет
                следующей, если сейчас перерыв (номер текущей пары = -1). Объект типа datetime.

    :return: порядковый номер пары, которая проходит в данный момент времени.
             Для пар, проводимых в нестандартное время (например, физ-ра или
             некоторые консультации), функция возвращает дробное число. Например,
             если какая-то пара проходит во временном промежутке между началом
             2-ой пары и концом 3-ей пары, причём границы этого временного
             промежутка не равны границам временного промежутка ни 2-ой, ни 3-ей
             пары, то функция вернёт 2.5. Если прямо сейчас никаких пар не проходит,
             функция вернёт None. Если данные для указанной беседы не были
             загружены, функция также возвращает None.
    """
    if now is None:
        return None

    # Если now для этой беседы не None, то и class_ordinals для неё тоже гарантированно не None.
    #
    # Проходимся по нумерации с конца для того, чтобы код работал корректно в ситуациях, когда в
    # нумерации у данной беседы есть пары, проводимые в нестандартное время (например, 3.5). Если
    # проходиться по class_ordinals#keys() в исходном порядке, то код будет отдавать предпочтение
    # парам, проводимым в нестандартное время.
    #
    # Пример: пусть у беседы настроена такая нумерация пар:
    #
    #         12.00-13.30: 3
    #         12.40-14.10: 3.5
    #         13.40-15.10: 4
    #         15.20-16.50: 5
    #
    # Если сейчас на часах, скажем, 13.45, то пройдясь по вышеуказанному списку с начала, можно сделать
    # вывод, что сейчас проходит пара с номером 3.5 (т.к. 13.45 лежит в промежутке 12.40-14.10, который
    # соответствует этому номеру пары, и мы упираемся в этот временной промежуток раньше других). Во
    # избежание подобных ситуаций мы проходим список с конца - в этом случае номером текущей пары будет 4.
    #
    # Это важно потому, что для обоих случаев (3.5 и 4 пара) следующей должна быть пара номер 5 (исходя из
    # приведённого выше списка) - те, кто сейчас сидит на паре номер 3.5, физически не могут иметь своей
    # следующей парой пару номер 4, т.к. время окончания пары номер 3.5 лежит во временном промежутке времени
    # проведения пары номер 4. Обход списка с конца позволяет избежать подобных ошибок.
    class_ordinals = tt_data.class_ordinals[chat]
    reversed_ordinals = reversed(sorted(class_ordinals.keys()))

    for start_tstr, end_tstr in reversed_ordinals:
        if is_cur_time_in_range(tt_data, chat, now, start_tstr, end_tstr):
            return class_ordinals[(start_tstr, end_tstr)]

    return None


def time_left_ru(hours_left, minutes_left, seconds_left):
    """
    Трансформирует указанное число часов, минут и секунд в человекочитаемый формат.

    :param hours_left: Оставшееся количество часов.
    :param minutes_left: Оставшееся количество минут.
    :param seconds_left: Оставшееся количество секунд.

    :return: время, оставшееся до какого-то момента в будущем, в человекочитаемом формате
             (см. функцию time_left). Если указанный момент уже наступил (число часов и минут
             равно нулю или отрицательно), поведение не определено - перед вызовом этой функции
             необходимо сделать проверку.
    """
    # Для менее точного, но более "юзер-френдли" вывода (чтобы от 1.02 до 1.05 было 3, а не 2 минуты).
    # Необходимо, т.к. мы не выводим секунды.
    if seconds_left != 0:
        minutes_left += 1

    result = ''

    if hours_left > 0:
        result += str(hours_left) + ' '
        last_digit = hours_left % 10

        if last_digit == 1 and hours_left != 11:  # "1, 21, 31, ... час", НО "11 часов"
            result += 'час'
        elif 2 <= last_digit <= 4 and not 12 <= hours_left <= 14:  # "2, 22, 32, ... часа", НО "12 часов"
            result += 'часа'
        else:
            result += 'часов'

        if minutes_left > 0:
            result += ' '

    # Не указываем минуты, если осталось целое количество часов.
    # Стоит отметить, что если осталось 0 час. и 0 мин, значит, время
    # уже наступило. В этом случае поведение функции не определено.
    if hours_left == 0 or minutes_left > 0:
        result += str(minutes_left) + ' '
        last_digit = minutes_left % 10

        if last_digit == 1 and minutes_left != 11:  # "1, 21, 31, ... минута", НО "11 минут"
            result += 'минута'
        elif 2 <= last_digit <= 4 and not 12 <= minutes_left <= 14:  # "2, 22, 32, ... минуты", НО "12 минут"
            result += 'минуты'
        else:
            result += 'минут'

    return result


def time_left_raw(tt_data, chat, future_tstr):
    """
    Вычисляет время в сыром формате (tuple(int, int, int)), оставшееся до того,
    как часы пробьют указанное время. Если указанное время уже наступило, возвращает None.
    @ См. time_left_raw_seconds

    :param tt_data: Данные о расписаниях всех бесед (TimetableData).

    :param chat: ID беседы, на часовой пояс которой необходимо ориентироваться.

    :param future_tstr: Время в будущем (сегодняшний день), промежуток до которого необходимо
                        посчитать, например, '13.40' - "через сколько часов и минут сегодня наступит 13.40".

    :return: Интервал времени до указанного момента в будущем, если этот момент ещё не наступил,
             None в противном случае. Если функция возвращает не None, то это будет кортеж (tuple),
             состоящий из трёх элементов. В индексе 0 будет число часов, оставшееся до наступления
             указанного момента в будущем, в индексе 1 - число минут, а в индексе 2 - число секунд.
             Если данные для указанной беседы не были загружены, возвращает None.
    """
    seconds_left = time_left_raw_seconds(tt_data, chat, future_tstr)

    if seconds_left is None:
        return None

    hours_left = seconds_left // 3600
    seconds_left %= 3600
    minutes_left = seconds_left // 60
    seconds_left %= 60

    return hours_left, minutes_left, seconds_left


def time_left_raw_seconds(tt_data, chat, future_tstr):
    """
    Вычисляет время в секундах, оставшееся до того,
    как часы пробьют указанное время. Если указанное время уже наступило, возвращает None.
    @ См. time_left_raw

    :param tt_data: Данные о расписаниях всех бесед (TimetableData).

    :param chat: ID беседы, на часовой пояс которой необходимо ориентироваться.

    :param future_tstr: Время в будущем (сегодняшний день), промежуток до которого необходимо
                        посчитать, например, '13.40' - "через сколько часов и минут сегодня наступит 13.40".

    :return: Количество секунд до указанного момента в будущем, если этот момент ещё не наступил,
             None в противном случае. Если функция возвращает не None, то это будет целое число (int),
             Если данные для указанной беседы не были загружены, возвращает None.
    """
    now = curtime(tt_data, chat)

    if now is None:
        return None

    # Если now для этой беседы не None, то и tz для неё тоже гарантированно не None.
    tz = tt_data.timezones[chat]

    future = now.combine(now.date(), datetime.strptime(future_tstr, timetable_parser.CLASS_TIME_FMT).time())
    future = tz.localize(future)

    if now >= future:
        # Указанное время не является временем в будущем - оно уже наступило.
        return None

    left = future - now

    return left.seconds


def time_left(tt_data, chat, future_tstr):
    """
    Вычисляет время в человекочитаемом формате (str - часы и минуты), оставшееся до того,
    как часы пробьют указанное время. Если указанное время уже наступило, возвращает None.

    :param tt_data: Данные о расписаниях всех бесед (TimetableData).

    :param chat: ID беседы, на часовой пояс которой необходимо ориентироваться.

    :param future_tstr: Время в будущем (сегодняшний день), промежуток до которого необходимо
                        посчитать, например, '13.40' - "через сколько часов и минут сегодня наступит 13.40".

    :return: Интервал времени до указанного момента в будущем, если этот момент ещё не наступил,
             None в противном случае. Если функция возвращает не None, то это будет строка (str)
             в легко читаемом человеком формате на русском языке, причём: если до указанного момента
             в будущем осталось менее часа, количество оставшихся часов (0) не указывается; если до
             указанного момента в будущем осталось ровное количество часов, то количество оставшихся
             минут (0) не указывается; если до указанного момента в будущем осталось, скажем, M
             минут и S секунд, функция опустит секунды и будет считать, что до этого момента осталось
             M+1 минут - это нужно для того, чтобы вывод "совпадал" с часами пользователей вида ЧАС:МИН.
             Если данные для указанной беседы не были загружены, возвращает None.
    """
    t = time_left_raw(tt_data, chat, future_tstr)
    return None if t is None else time_left_ru(t[0], t[1], t[2])


def next_class(tt_data, chat_id, groups):
    """
    Ищет данные предстоящей для некоторого студента пары (ClassData) с учётом чётности текущей недели.

    :param tt_data: Данные о расписаниях всех бесед (TimetableData).

    :param chat_id: ID беседы, в котором состоит этот студент (число).

    :param groups: Список групп, в которых состоит какой-то конкретный студент.
                   Используется для определения расписания для этого студента.

    :return: информация о паре (ClassData) которая должна быть следующей по расписанию для
             некоторого студента, который состоит в группах groups. Если такому студенту
             сегодня больше не предстоит никаких пар, возвращает None. Текущая неделя
             ("верхняя" или "нижняя") также учитывается. Если данные для указанной беседы
             не были загружены, возвращает None.
    """
    now = curtime(tt_data, chat_id)

    if now is None:
        return None

    # Если now для этой беседы не None, то всё остальное тоже гарантированно будет не None.
    cur_class_ordinal = class_ordinal(tt_data, chat_id, now)

    if cur_class_ordinal is None:
        # Возможно, сейчас перерыв между парами. Перерыв не может быть дольше MAX_BREAK_LEN_MINS минут.
        # Значит, последняя пара проходила не более чем (MAX_BREAK_LEN_MINS + 5) минут назад.
        # Под "проходила" здесь подразумевается возможность проведения какой-либо пары в это
        # время в целом (её наличие в таблице CLASS_ORDINALS) - без учёта реального расписания.
        cur_class_ordinal = class_ordinal(tt_data, chat_id, now - timedelta(minutes=(MAX_BREAK_LEN_MINS + 5)))

        if cur_class_ordinal is None:
            # Учебный день закончился. Дальше сегодня точно не будет никаких пар.
            return None

    day_of_week = weekday_ru(tt_data, chat_id)

    # Зная реальное расписание, порядковый номер текущей пары и группы, в которых
    # состоит некоторый студент, ищем данные о предстоящей для него паре. Если такой
    # пары не находится, значит, на сегодня учебный день для этого студента закончен.
    class_ordinals = tt_data.class_ordinals[chat_id]

    for start_tstr, end_tstr in class_ordinals.keys():
        if class_ordinals[(start_tstr, end_tstr)] > cur_class_ordinal:
            next_class_data = get_class(tt_data, chat_id, day_of_week, start_tstr, end_tstr, groups)

            if next_class_data is not None:
                return next_class_data

    return None


def _is_member(target_groups, groups):
    """
    Используется для проверки того, касается ли текущая пара некоторого студента.
    Выбрасывает TypeError, если переданы аргументы некорректных типов.

    :param target_groups: Каких групп должна коснуться эта пара. Функция вернёт True только в случае
                          если хотя бы одна из групп в списке target_groups есть также и в в списке
                          groups, т.е. студент состоит хотя бы в одной из групп из списка target_groups.

    :param groups: Список групп, в которых состоит какой-то конкретный студент.
                   Используется для определения расписания для этого студента.

    :return: True, если некоторый студент, состоящий в группах, указанных в списке groups,
             состоит в группе или группах target_groups, False в противном случае.
    """
    if type(groups) != list and type(groups) != tuple:
        raise TypeError('invalid groups parameter: expected one of: '
                        '[list, tuple], but got: %s' % type(groups))

    if type(target_groups) == list or type(target_groups) == tuple:
        return any(group in groups for group in target_groups)
    else:
        raise TypeError('invalid target_groups parameter: expected one of: '
                        '[list, tuple], but got: %s' % type(target_groups))


def get_all_classes(tt_data, chat_id, weekday, groups):
    """
    Ищет данные всех пар (List[ClassData]), которые должны быть
    за день у некоторого студента с учётом чётности текущей недели.

    @ См. функцию get_class.

    :param tt_data: Данные о расписаниях всех бесед (TimetableData).

    :param chat_id: ID беседы, в котором состоит этот студент (число).

    :param weekday: День недели на русском ('Понедельник', 'Вторник', ...).
                    @ См. функцию weekday_ru.

    :param groups: Список групп, в которых состоит какой-то конкретный студент.
                   Используется для определения расписания для этого студента.

    :return: данные всех пар (List[ClassData]), которые должны проходить за день для некоторого
             студента, который состоит в группах groups. Если в это время для такого
             студента никаких пар нет, возвращает пустой список. Текущая неделя ("верхняя" или
             "нижняя") также учитывается. Если файл с расписанием для указанной беседы
             не был успешно загружен (load_failed), эта функция всегда возвращает пустой список.
             То же самое будет, если ещё не выполнялся load. (Эта функция никогда не возвращает None.)
    """
    try:
        cur_week = get_week(tt_data, chat_id)

        if cur_week is None:
            return []

        # Если cur_week для этой беседы не None, то и classes для неё тоже гарантированно не None.
        classes = tt_data.classes[chat_id].get(weekday, None)

        if classes is None:
            # В ЭТОТ ДЕНЬ НЕДЕЛИ для указанной беседы нет никаких пар.
            return []

        result = []

        for class_data in classes:
            if (class_data.week is None or class_data.week == cur_week) \
                    and (class_data.target_groups is None or _is_member(class_data.target_groups, groups)):
                result.append(class_data)

        return result
    except KeyError:
        return []


def get_class(tt_data, chat_id, weekday, start_tstr, end_tstr, groups):
    """
    Ищет данные пары (ClassData), которая сейчас должна быть у некоторого студента с учётом чётности текущей недели.
    @ См. функцию _is_member.

    :param tt_data: Данные о расписаниях всех бесед (TimetableData).

    :param chat_id: ID беседы, в котором состоит этот студент (число).

    :param weekday: День недели на русском ('Понедельник', 'Вторник', ...).
                    @ См. функцию weekday_ru.

    :param start_tstr: Время начала пары, строка. Например, '13.40'.

    :param end_tstr: Время окончания пары, строка. Например, '15.10'.

    :param groups: Список групп, в которых состоит какой-то конкретный студент.
                   Используется для определения расписания для этого студента.

    :return: данные пары (ClassData), которая должна проходить в указанное время для некоторого
             студента, который состоит в группах groups. Если в это время для такого
             студента никаких пар нет, возвращает None. Текущая неделя ("верхняя" или
             "нижняя") также учитывается. Если файл с расписанием для указанной беседы
             не был успешно загружен (load_failed), эта функция всегда возвращает None.
             То же самое будет, если ещё не выполнялся load.
    """
    try:
        cur_week = get_week(tt_data, chat_id)

        if cur_week is None:
            return None

        # Если cur_week для этой беседы не None, то и classes для неё тоже гарантированно не None.
        classes = tt_data.classes[chat_id].get(weekday, None)

        if classes is None:
            # В ЭТОТ ДЕНЬ НЕДЕЛИ для указанной беседы нет никаких пар.
            return None

        for class_data in classes:
            if class_data.start_tstr == start_tstr and class_data.end_tstr == end_tstr:
                if (class_data.week is None or class_data.week == cur_week) \
                        and (class_data.target_groups is None or _is_member(class_data.target_groups, groups)):
                    return class_data

        return None
    except KeyError:
        return None
