import os
import traceback

import yaml


# TODO Хранить расписания для каждой беседы ВРЕМЕННО.
#      При неактивности удалять из памяти и подгружать по необходимости.
global timetables


TIMETABLE_FILE_EXT = '.yml'


def load_all():
    global timetables
    timetables = {}

    for file in os.listdir('timetables'):
        if file.endswith(TIMETABLE_FILE_EXT):
            with open('timetables/' + file, 'r', encoding='UTF-8') as fstream:
                try:
                    owner_chat_id = int(file[:-len(TIMETABLE_FILE_EXT)])
                    timetable = yaml.safe_load(fstream)
                    __parse(timetable)
                except ValueError:
                    print('Skipped file with invalid name %s: '
                          'expected CHAT_ID_INT%s' % (file, TIMETABLE_FILE_EXT))
                except yaml.YAMLError:
                    print('Failed to read file %s. Skipping it. '
                          'Timetables will not function for chat %i. Details:' % (file, owner_chat_id))
                    traceback.print_exc()


def __parse(timetable):



class ClassData:
    """
    Объект для хранения данных о парах.
    """

    def __init__(self, name, auditorium, educator):
        """
        Создаёт новый объект данных о паре.
        """
        self.name = name
        self.auditorium = auditorium
        self.educator = educator

    def __str__(self):
        return '%s в ауд. %s (%s)' % (self.name, self.auditorium, self.educator)
