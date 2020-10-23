import datetime
import os
import time
import traceback

import yaml


global timetables, load_failed


TIMETABLE_FILE_EXT = '.yml'
WEEKDAYS_RU = {
    0: 'Понедельник',
    1: 'Вторник',
    2: 'Среда',
    3: 'Четверг',
    4: 'Пятница',
    5: 'Суббота',
    6: 'Воскресенье',
}


def weekday_ru():
    """
    Возвращает название текущего дня недели на русском языке ('Понедельник', 'Вторник', ...).
    :return: строка, содержащая текущий день недели, которая может быть использована в функции get_class.
    """
    return WEEKDAYS_RU[datetime.datetime.today().weekday()]


def get_week():
    """
    Проверяет, верхняя (нечётная) или нижняя (чётная) ли сейчас неделя.
    :return: 'верхняя', если текущая неделя верхняя (нечётная), 'нижняя', если текущая неделя нижняя (чётная).
    """
    return 'нижняя' if int(time.strftime("%U", time.gmtime())) % 2 == 0 else 'верхняя'


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

    global timetables

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
        return '%s в ауд. %i (%s)' % (self.name, self.auditorium, self.educator)
