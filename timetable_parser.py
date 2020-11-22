import os
import re
import traceback

import pytz
import yaml


# TODO Хранить расписания для каждой беседы ВРЕМЕННО.
#      При неактивности удалять из памяти и подгружать по необходимости.
global timezones, class_ordinals, classes


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

TIMETABLE_FILE_EXT = '.yml'
GMT_TIMEZONE_REGEX = r'GMT[+-]\d{1,2}'
CLASS_ORDINALS_TIME_REGEX = r'^(\d{2}\.\d{2})-(\d{2}\.\d{2})$'  # HH.mm-HH.mm; выделяет время начала и время конца

# Формат времени проведения пар в файлах с расписаниями.
CLASS_TIME_FMT = '%H.%M'


def load_all(send):
    """
    Загружает все файлы с расписаниями из папки timetables, парсит их, проверяет на ошибки и затем
    извлекает нужные данные обо всех беседах в память. Если данные уже были загружены, все они будут
    загружены заново (т.е. функцию можно вызвать повторно для перезагрузки данных с диска). Если данные
    какой-либо беседы не удалось загрузить, то весь функционал, связанный с расписанием, для этой беседы
    будет недоступен, а в беседу будет отправлена соответствующее сообщение об ошибке.

    :param send: Функция для отправки сообщений в беседу.
    """
    global timezones, class_ordinals, classes

    timezones = {}
    class_ordinals = {}
    classes = {}

    for file in os.listdir('timetables'):
        if file.endswith(TIMETABLE_FILE_EXT):
            with open('timetables/' + file, 'r', encoding='UTF-8') as fstream:
                try:
                    owner_chat_id = int(file[:-len(TIMETABLE_FILE_EXT)])
                    timetable_yml = yaml.safe_load(fstream)

                    # noinspection PyBroadException
                    try:
                        __parse_all(owner_chat_id, timetable_yml)
                        print('Loaded timetable file for chat %i' % owner_chat_id)
                    except Exception as e:
                        print('Failed to parse file %s (invalid syntax). Skipping it. '
                              'Timetables will not function for chat %i. Details:' % (file, owner_chat_id))

                        if isinstance(e, SyntaxError):
                            print(e)
                            send(owner_chat_id + 2E9, '⚠ Не удалось загрузить файл с расписанием для этой беседы, '
                                                      'поскольку он составлен неверно: ' + str(e))
                        else:
                            traceback.print_exc()
                            send(owner_chat_id + 2E9, '⚠ Не удалось загрузить файл с расписанием для этой беседы '
                                                      'из-за непредвиденной ошибки:\n\n' + traceback.format_exc())

                        # Удаляем данные, которые могли загрузиться для этой беседы до появления ошибки,
                        # чтобы для этой беседы нельзя было использовать связанный с расписанием функционал.
                        if owner_chat_id in timezones:
                            del timezones[owner_chat_id]

                        if owner_chat_id in class_ordinals:
                            del class_ordinals[owner_chat_id]

                        if owner_chat_id in classes:
                            del classes[owner_chat_id]
                except ValueError:
                    print('Skipped file with invalid name %s: '
                          'expected CHAT_ID_INT%s' % (file, TIMETABLE_FILE_EXT))
                except yaml.YAMLError:
                    print('Failed to read file %s. Skipping it. '
                          'Timetables will not function for chat %i. Details:' % (file, owner_chat_id))
                    traceback.print_exc()


def __parse_all(chat, yml):
    __parse_timezone(chat, yml)
    __parse_class_ordinals(chat, yml)
    __parse_timetables(chat, yml)


def __parse_timezone(chat, yml):
    global timezones

    try:
        tz_str = yml['Часовой пояс']

        if not re.fullmatch(GMT_TIMEZONE_REGEX, tz_str):
            raise SyntaxError('некорректно указан часовой пояс: "%s"; '
                              'формат: "GMT+H" или "GMT-H" (H ≤ 12) (например, "GMT+3" для Москвы)'
                              % tz_str)

        # Заменяем (например) "GMT+2" на "GMT-2". Это нужно, т.к. в pytz перепутаны коды
        # часовых поясов - там, где должен быть "+", в библиотеке стоит "-", и наоборот.
        if '+' in tz_str:
            tz_str = tz_str.replace('+', '-')
        else:
            tz_str = tz_str.replace('-', '+')

        try:
            timezones[chat] = pytz.timezone('Etc/' + tz_str)
        except pytz.UnknownTimeZoneError:
            raise SyntaxError('указан неизвестный часовой пояс (вы точно с этой планеты?); '
                              'формат: "GMT+H" или "GMT-H" (H ≤ 12) (например, "GMT+3" для Москвы)')

    except KeyError:
        raise SyntaxError('отсутствует обязательное поле "Часовой пояс"')


def __parse_class_ordinals(chat, yml):
    global class_ordinals
    class_ordinals[chat] = {}

    try:
        ordinals = yml['Нумерация']
    except KeyError:
        raise SyntaxError('отсутствует обязательный раздел "Нумерация"')

    if len(ordinals) == 0:
        raise SyntaxError('раздел "Нумерация" не может быть пустым')

    for time_str in ordinals.keys():
        time_groups = re.search(CLASS_ORDINALS_TIME_REGEX, time_str)

        if time_groups is None:
            raise SyntaxError('некорректно указано время проведения пары в нумерации: "%s" — формат: "ЧЧ.мм-ЧЧ.мм"; '
                              'обратите внимание, что задавать время как "8.00" недопустимо — нужно писать "08.00"'
                              % time_str)

        start_tstr = time_groups.group(1)
        end_tstr = time_groups.group(2)
        ordinal_str = ordinals[time_str]

        try:
            ordinal = float(ordinal_str)
        except ValueError:
            raise SyntaxError('некорректно указан номер пары ("%s"), проходящей во временной промежуток "%s" — '
                              'ожидалось целое число или десятичная дробь (например, 3.5 — через точку!)'
                              % (ordinal_str, time_str))

        for _start_tstr, _end_tstr in class_ordinals[chat].keys():
            if class_ordinals[chat][(_start_tstr, _end_tstr)] == ordinal:
                raise SyntaxError('пары, проходящие в разное время ("%s-%s" и "%s-%s"), '
                                  'имеют одинаковый порядковый номер %s'
                                  % (_start_tstr, _end_tstr, start_tstr, end_tstr, ordinal))

        class_ordinals[chat][(start_tstr, end_tstr)] = ordinal


def __parse_timetables(chat, yml):
    global classes
    classes[chat] = {}

    for section in yml.keys():
        if section in WEEKDAYS_RU.values():
            __parse_timetable(chat, yml, section)
        elif section != 'Часовой пояс' and section != 'Нумерация':
            raise SyntaxError('недопустимый раздел "%s"; обратите внимание, что дни недели должны '
                              'быть записаны по-русски с заглавной буквы (например, "Понедельник")'
                              % section)


def __parse_timetable(chat, yml, weekday):
    global classes
    classes[chat][weekday] = []

    for time_str in yml[weekday].keys():
        time_groups = re.search(CLASS_ORDINALS_TIME_REGEX, time_str)

        if time_groups is None:
            raise SyntaxError('некорректно указано время проведения пары в день %s: "%s" — формат: "ЧЧ.мм-ЧЧ.мм"; '
                              'обратите внимание, что задавать время как "8.00" недопустимо — нужно писать "08.00"'
                              % (weekday, time_str))

        start_tstr = time_groups.group(1)
        end_tstr = time_groups.group(2)

        if (start_tstr, end_tstr) not in class_ordinals[chat]:
            raise SyntaxError('некорректно указано время проведения пары в день %s: "%s" — '
                              'такого временного промежутка нет в разделе "Нумерация"'
                              % (weekday, time_str))

        for class_name in yml[weekday][time_str].keys():
            class_data = yml[weekday][time_str][class_name]

            try:
                host = class_data['Преподаватель']
            except KeyError:
                raise SyntaxError('для пары "%s", проходящей в %s в день %s, '
                                  'отсутствует обязательное поле "Преподаватель"'
                                  % (class_name, time_str, weekday))

            try:
                aud = class_data['Аудитория']
            except KeyError:
                raise SyntaxError('для пары "%s", проходящей в %s в день %s, '
                                  'отсутствует обязательное поле "Аудитория"'
                                  % (class_name, time_str, weekday))

            week = class_data.get('Неделя', None)
            target_groups = class_data.get('Группы', None)

            if target_groups is not None and type(target_groups) == str:
                # Преобразуем поля вида "Группы: единственная_группа" в список
                # с единственным элементом (чтобы в дальнейшем было удобнее работать).
                target_groups = [target_groups]

            classes[chat][weekday].append(ClassData(
                start_tstr, end_tstr, class_name, host, aud, week, target_groups))


class ClassData:
    """
    Объект для хранения данных о парах.
    """

    def __init__(self, start_tstr, end_tstr, name, host, aud, week, target_groups):
        """
        Создаёт новый объект данных о паре.
        """
        self.start_tstr = start_tstr
        self.end_tstr = end_tstr
        self.name = name
        self.host = host
        self.aud = aud
        self.week = week
        self.target_groups = target_groups

    def __str__(self):
        return '%s в %s в ауд. %s (%s)' % (self.name, self.start_tstr, self.aud, self.host)
