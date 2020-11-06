from datetime import (
    datetime,
    timedelta
)

import os
import time
import traceback

import yaml
import pytz


global timetables, load_failed


# Часовой пояс в Калининграде (UTC+2).
KALININGRAD_TZ = pytz.timezone('Etc/GMT+2')

# Наибольшая продолжительность перерыва между парами в минутах.
MAX_BREAK_LEN_MINS = 30

# Расширение файлов с расписаниями.
TIMETABLE_FILE_EXT = '.yml'

# Формат времени проведения пар в файлах с расписаниями.
CLASS_TIME_FMT = '%H.%M'

# Таблица времени проведения пар к их порядковому номеру.
# Пары, проводимые в нестандартное время, имеют дробные номера.
CLASS_ORDINALS = {
    ('00.00', '08.29'): 0,
    ('08.30', '10.00'): 1,
    ('10.10', '11.40'): 2,
    ('11.10', '12.40'): 2.5,
    ('12.00', '13.30'): 3,
    ('12.40', '14.10'): 3.5,
    ('13.40', '15.10'): 4,
    ('15.20', '16.50'): 5,
    ('17.00', '18.30'): 6,
    ('18.40', '20.10'): 7,
    ('20.00', '21.00'): 7.5
}

# Таблица номеров дней недели (0..6) к их названию на русском.
WEEKDAYS_RU = {
    0: 'Понедельник',
    1: 'Вторник',
    2: 'Среда',
    3: 'Четверг',
    4: 'Пятница',
    5: 'Суббота',
    6: 'Воскресенье',
}


def curtime_utc2():
    """
    Возвращает текущее время в часовом поясе UTC+2.
    :return: объект datetime, соответствующий текущему времени в Калининграде.
    """
    return datetime.now().replace(tzinfo=KALININGRAD_TZ)


def weekday_ru():
    """
    Возвращает название текущего дня недели на русском языке ('Понедельник', 'Вторник', ...).
    :return: строка, содержащая текущий день недели, которая может быть использована в функции get_class.
    """
    return WEEKDAYS_RU[datetime.today().weekday()]


def get_week():
    """
    Проверяет, верхняя (нечётная) или нижняя (чётная) ли сейчас неделя.
    :return: 'верхняя', если текущая неделя верхняя (нечётная), 'нижняя', если текущая неделя нижняя (чётная).
    """
    return 'нижняя' if int(time.strftime("%W", time.gmtime(time.time() + 2*60*60))) % 2 == 0 else 'верхняя'


def __is_cur_time_in_range(now, start_tstr, end_tstr):
    """
    Проверяет, находится ли текущее время в указанном временном диапазоне.

    :param now: Текущее время - datetime. Передаётся для того, чтобы не вычислять
                curtime_utc2() несколько раз за одну серию обращений.

    :param start_tstr: Начало временного диапазона - str (например, '13.30').

    :param end_tstr: Конец временного диапазона - str (например, '21.05').

    :return: True, если текущее время находится в указанном временном диапазоне,
             False в противном случае.
    """
    start = KALININGRAD_TZ.localize(now.combine(now.date(),
                                                datetime.strptime(start_tstr, CLASS_TIME_FMT).time()))
    end = KALININGRAD_TZ.localize(now.combine(now.date(),
                                              datetime.strptime(end_tstr, CLASS_TIME_FMT).time()))

    return start <= now.replace(tzinfo=KALININGRAD_TZ) <= end


def class_ordinal(now):
    """
    Возвращает порядковый номер пары, которая проходит в указанный момент времени.

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
             функция вернёт -1 (0, если пары ещё не начались, т.е. сейчас время
             от 0.00 до 8.29 включительно).
    """
    for start_tstr, end_tstr in CLASS_ORDINALS.keys():
        if __is_cur_time_in_range(now, start_tstr, end_tstr):
            return CLASS_ORDINALS[(start_tstr, end_tstr)]

    return -1


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


def time_left(future_tstr):
    """
    Вычисляет время в человекочитаемом формате (str - часы и минуты), оставшееся до того,
    как часы пробьют указанное время. Если указанное время уже наступило, возвращает None.

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
    """
    now = curtime_utc2()
    future = now.combine(now.date(), datetime.strptime(future_tstr, CLASS_TIME_FMT).time())
    future = KALININGRAD_TZ.localize(future)

    print('now:')
    print(now)
    print('now2:')
    print(now.replace(tzinfo=KALININGRAD_TZ))
    print('future:')
    print(future)

    if now >= future:
        # Указанное время не является временем в будущем - оно уже наступило.
        return None

    left = future - now

    seconds_left = left.seconds
    hours_left = seconds_left // 3600
    seconds_left %= 3600
    minutes_left = seconds_left // 60
    seconds_left %= 60

    return time_left_ru(hours_left, minutes_left, seconds_left)


def next_class(chat_id, groups):
    """
    Ищет данные предстоящей для некоторого студента пары (ClassData) с учётом чётности текущей недели,
    а также время начала этой пары (например, '13.40'). Возвращает список (tuple), в индексе 0 которого
    находятся данные о следующей паре (ClassData), а в индексе 1 - время её начала (str). Если не удалось
    найти подходящую пару, функция возвращает None вместо списка.

    :param chat_id: ID беседы, в котором состоит этот студент (число).

    :param groups: Список групп, в которых состоит какой-то конкретный студент.
                   Используется для определения расписания для этого студента.

    :return: информация о паре, которая должна быть следующей по расписанию для
             некоторого студента, который состоит в группах groups. Если такому студенту
             сегодня больше не предстоит никаких пар, возвращает None. Текущая неделя
             ("верхняя" или "нижняя") также учитывается. Если файл с расписанием для
             указанной беседы не был успешно загружен (load_failed), эта функция всегда
             возвращает None. То же самое будет, если ещё не выполнялся load.
    """
    if chat_id in load_failed:
        return None

    now = curtime_utc2()
    cur_class_ordinal = class_ordinal(now)

    if cur_class_ordinal == -1:
        # Возможно, сейчас перерыв между парами. Перерыв не может быть дольше MAX_BREAK_LEN_MINS минут.
        # Значит, последняя пара проходила не более чем (MAX_BREAK_LEN_MINS + 5) минут назад.
        # Под "проходила" здесь подразумевается возможность проведения какой-либо пары в это
        # время в целом (её наличие в таблице CLASS_ORDINALS) - без учёта реального расписания.
        cur_class_ordinal = class_ordinal(now - timedelta(minutes=(MAX_BREAK_LEN_MINS + 5)))

        if cur_class_ordinal == -1:
            # Учебный день закончился. Дальше сегодня точно не будет никаких пар.
            return None

    day_of_week = weekday_ru()

    # Зная реальное расписание, порядковый номер текущей пары и группы, в которых
    # состоит некоторый студент, ищем данные о предстоящей для него паре. Если такой
    # пары не находится, значит, на сегодня учебный день для этого студента закончен.
    for start_tstr, end_tstr in CLASS_ORDINALS.keys():
        if CLASS_ORDINALS[(start_tstr, end_tstr)] > cur_class_ordinal:
            next_class_data = get_class(chat_id, day_of_week, start_tstr + '-' + end_tstr, groups)

            if next_class_data is not None:
                return next_class_data, start_tstr

    return None


def __is_member(target_groups, groups):
    """
    Используется для проверки того, касается ли текущая пара некоторого студента.
    Выбрасывает TypeError, если переданы аргументы некорректных типов.

    :param target_groups: Каких групп должна коснуться эта пара. 1) Если этот параметр - строка, то
                          функция вернёт True только в случае, если в переданном списке групп студента
                          есть группа с названием target_groups, т.е. студент состоит в группе target_groups.
                          2) Если этот параметр - список (list или tuple), тогда эта функция вернёт True только
                          в случае, если хотя бы одна из групп в списке target_groups есть также и в в списке
                          groups, т.е. студент состоит хотя бы в одной из групп из списка target_groups.

    :param groups: Список групп, в которых состоит какой-то конкретный студент.
                   Используется для определения расписания для этого студента.

    :return: True, если некоторый студент, состоящий в группах, указанных в списке groups,
             состоит в группе или группах target_groups, False в противном случае.
    """
    if type(groups) != list and type(groups) != tuple:
        raise TypeError('invalid groups parameter: expected one of: '
                        '[list, tuple], but got: %s' % type(groups))

    if type(target_groups) == str:
        return target_groups in groups
    elif type(target_groups) == list or type(target_groups) == tuple:
        return any(group in groups for group in target_groups)
    else:
        raise TypeError('invalid target_groups parameter: '
                        'expected one of: [str, list, tuple], but got: %s' % type(target_groups))


def get_class(chat_id, day_of_week, class_time, groups):
    """
    Ищет данные пары (ClassData), которая сейчас должна быть у некоторого студента с учётом чётности текущей недели.
    Выбрасывает RuntimeError, если загруженный файл с расписанием для указанной беседы составлен с ошибками.
    @ См. функцию __is_member.

    :param chat_id: ID беседы, в котором состоит этот студент (число).

    :param day_of_week: День недели на русском ('Понедельник', 'Вторник', ...).
                        @ См. функцию weekday_ru.

    :param class_time: Строка вида 'HH.mm-HH.mm', ообозначающая период прохождения пары
                       ('13.40-15.10' - с 13:40 до 15:10).

    :param groups: Список групп, в которых состоит какой-то конкретный студент.
                   Используется для определения расписания для этого студента.

    :return: данные пары (ClassData), которая должна проходить в указанное время для некоторого
             студента, который состоит в группах groups. Если в это время для такого
             студента никаких пар нет, возвращает None. Текущая неделя ("верхняя" или
             "нижняя") также учитывается. Если файл с расписанием для указанной беседы
             не был успешно загружен (load_failed), эта функция всегда возвращает None.
             То же самое будет, если ещё не выполнялся load.
    """
    if chat_id in load_failed:
        return None

    try:
        class_nodes = timetables[chat_id][day_of_week][class_time]

        if class_nodes is None or len(class_nodes) == 0:
            raise RuntimeError('invalid timetable: missing class nodes in "timetables/%i%s" ("%s" -> "%s")'
                               % (chat_id, TIMETABLE_FILE_EXT, day_of_week, class_time))

        cur_week = get_week()

        for class_name in class_nodes.keys():
            target_groups = class_nodes[class_name].get('Группы', None)
            week = class_nodes[class_name].get('Неделя', None)

            if (week is None or week == cur_week) \
                    and (target_groups is None or __is_member(target_groups, groups)):
                class_data = class_nodes[class_name]
                return ClassData(class_name, class_data['Аудитория'], class_data['Преподаватель'])

        return None
    except KeyError:
        return None


def load():
    """
    Загружает все файлы с расписанием из папки 'timetables'.

    Файлы с расширением, отличным от того, что указано в TIMETABLE_FILE_EXT, игнорируются.
    Если название какого-то файла не является целым числом (допустимым ID беседы), он будет пропущен;
    при этом будет выведено предупреждение. Если какой-то файл не удаётся загрузить, он будет пропущен;
    при этом будет выведено предупреждение; кроме того, все последующие вызовы функции get_class для
    беседы, которой соответствует этот файл, будут возвращать None.

    Повторное использование load приведёт к перезагрузке всех файлов с расписанием, в том числе тех,
    которые не удалось загрузить до этого. Старый список load_failed при этом будет очищен.
    """
    global timetables, load_failed

    timetables = {}
    load_failed = []

    for file in os.listdir('timetables'):
        if file.endswith(TIMETABLE_FILE_EXT):
            with open('timetables/' + file, 'r', encoding='UTF-8') as fstream:
                try:
                    owner_chat_id = int(file[:-len(TIMETABLE_FILE_EXT)])
                    timetables[owner_chat_id] = yaml.safe_load(fstream)
                except ValueError:
                    print('Skipped file with invalid name %s: '
                          'expected CHAT_ID_INT%s' % (file, TIMETABLE_FILE_EXT))
                except yaml.YAMLError:
                    load_failed.append(owner_chat_id)
                    print('Failed to read file %s. Skipping it. '
                          'Timetables will not function for chat %i. Details:' % (file, owner_chat_id))
                    traceback.print_exc()


class ClassData:
    """
    Объект для хранения данных о парах.
    """

    def __init__(self, name, auditorium, educator):
        """
        Создаёт новый объект данных о паре.

        :param name: название или краткое описание пары.

        :param auditorium: номер аудиториии, в которой проходит пара, либо ссылка на вход,
                           если эта пара проходит дистанционно.

        :param: educator Фамилия и инициалы преподавателя.
        """
        self.name = name
        self.auditorium = auditorium
        self.educator = educator

    def __str__(self):
        return '%s в ауд. %s (%s)' % (self.name, self.auditorium, self.educator)
