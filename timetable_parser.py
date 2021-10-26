import re
import traceback

import urllib.request
from datetime import datetime

import pytz
import yaml

import log_util

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

# Максимальный размер файла с расписанием (пытаемся защищаться от дудосов маминых кулхацкеров).
MAX_TIMETABLE_FILE_LEN_BYTES = 32 * 1024  # 32 KiB


class TimetableData:
    # TODO 1: не хранить ВСЕ расписания в памяти (на далёкое будущее)
    # TODO 2: добавить возможность перезагружать файлы отдельных бесед
    def __init__(self, kristy):
        self.logger = log_util.init_logging(__name__)
        self.kristy = kristy
        self.timezones = {}
        self.class_ordinals = {}
        self.classes = {}

    def load_all(self):
        """
        Загружает все файлы с расписаниями по ссылкам из БД, парсит их, проверяет на ошибки и затем
        извлекает нужные данные обо всех беседах в память. Если данные уже были загружены, все они будут
        загружены заново (т.е. функцию можно вызвать повторно для перезагрузки данных с диска). Если данные
        какой-либо беседы не удалось загрузить, то весь функционал, связанный с расписанием, для этой беседы
        будет недоступен, а в беседу будет отправлена соответствующее сообщение об ошибке.

        См. _load_timetable
        """
        self.timezones = {}
        self.class_ordinals = {}
        self.classes = {}

        for chat in self.kristy.db.all_chat_ids():
            self.load_timetable(chat)

    def load_timetable(self, chat):
        """
        (Пере-)загружает файл с расписанием указанной беседы: получает ссылку на нужный файл
        из БД, затем, если эта ссылка есть (не null), пытается скачать по ней текстовый файл,
        декодировать его, загрузить как YAML и спарсить. В случае какой-либо ошибки, выведет
        информацию об этой ошибке в консоль и в беседу.

        :param chat: ID беседы, расписание которой необходимо (пере-)загрузить.
        """
        timetable_url = self.kristy.db.get_timetable_url(chat)

        if timetable_url:
            try:
                contents_str = urllib.request \
                    .urlopen(timetable_url) \
                    .read(MAX_TIMETABLE_FILE_LEN_BYTES) \
                    .decode('utf-8')

                timetable_yml = yaml.safe_load(contents_str)

                self._parse_timetable(chat, timetable_yml)
                self.logger.info('Загружен файл с расписанием беседы № %i', chat)
            except Exception as e:
                return  # TODO добавить потом, мешает
                self.logger.warning('Не удалось обработать файл с расписанием беседы № %i:', chat)

                if isinstance(e, SyntaxError):
                    self.logger.warning('%s', e)
                    self.kristy.send(chat + 2E9,
                                     '⚠ Не удалось загрузить файл с расписанием для '
                                     'этой беседы, поскольку он составлен неверно: ' + str(e))
                else:
                    traceback.print_exc()
                    self.kristy.send(chat + 2E9,
                                     '⚠ Не удалось загрузить файл с расписанием для этой беседы '
                                     'из-за непредвиденной ошибки:\n\n' + traceback.format_exc())

                # Удаляем данные, которые могли загрузиться для этой беседы до появления ошибки,
                # чтобы для этой беседы нельзя было использовать связанный с расписанием функционал.
                if chat in self.timezones:
                    del self.timezones[chat]

                if chat in self.class_ordinals:
                    del self.class_ordinals[chat]

                if chat in self.classes:
                    del self.classes[chat]
        else:
            self.logger.info('У беседы № %i не указана ссылка на файл с расписанием', chat)
            return  # TODO добавить потом, мешает
            self.kristy.send(chat + 2E9,
                             '⚠ Файл с расписанием для этой беседы не установлен. '
                             'Используйте "!расписание [ссылка]", чтобы исправить это.')

    def _parse_timetable(self, chat, yml):
        self._parse_timezone(chat, yml)
        self._parse_class_ordinals(chat, yml)
        self._parse_timetables(chat, yml)

    def _parse_timezone(self, chat, yml):
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
                self.timezones[chat] = pytz.timezone('Etc/' + tz_str)
            except pytz.UnknownTimeZoneError:
                raise SyntaxError('указан неизвестный часовой пояс (вы точно с этой планеты?); '
                                  'формат: "GMT+H" или "GMT-H" (H ≤ 12) (например, "GMT+3" для Москвы)')

        except KeyError:
            raise SyntaxError('отсутствует обязательное поле "Часовой пояс"')

    def _parse_class_ordinals(self, chat, yml):
        self.class_ordinals[chat] = {}

        try:
            ordinals = yml['Нумерация']
        except KeyError:
            raise SyntaxError('отсутствует обязательный раздел "Нумерация"')

        if len(ordinals) == 0:
            raise SyntaxError('раздел "Нумерация" не может быть пустым')

        prev_ordinal = 0

        for time_str in ordinals.keys():
            time_groups = re.search(CLASS_ORDINALS_TIME_REGEX, time_str)

            if time_groups is None:
                raise SyntaxError(
                    'некорректно указано время проведения пары в нумерации: "%s" — формат: "ЧЧ.мм-ЧЧ.мм"; '
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

            if ordinal < prev_ordinal:  # проверка на равенство делается чуть ниже сразу для всех номеров пар
                raise SyntaxError('пары пронумерованы не по порядку: %s < %s'
                                  % (ordinal, prev_ordinal))

            tz = self.timezones[chat]
            now = datetime.now(tz)
            dt = tz.localize(now.combine(now.date(),
                                         datetime.strptime(start_tstr, CLASS_TIME_FMT).time()))

            for _start_tstr, _end_tstr in self.class_ordinals[chat].keys():
                _ordinal = self.class_ordinals[chat][(_start_tstr, _end_tstr)]

                if ordinal == _ordinal:
                    raise SyntaxError('пары, проходящие в разное время ("%s-%s" и "%s-%s"), '
                                      'имеют одинаковый порядковый номер %s'
                                      % (_start_tstr, _end_tstr, start_tstr, end_tstr, ordinal))
                else:  # значит, ordinal > _ordinal ввиду прохождения проверки ordinal < prev_ordinal чуть выше
                    _dt = tz.localize(now.combine(now.date(),
                                                  datetime.strptime(_start_tstr, CLASS_TIME_FMT).time()))

                    if dt < _dt:
                        raise SyntaxError('пара "%s-%s" начинается раньше, чем "%s-%s", '
                                          'однако её порядковый номер выше (%s против %s)'
                                          % (start_tstr, end_tstr, _start_tstr, _end_tstr, ordinal, _ordinal))

            self.class_ordinals[chat][(start_tstr, end_tstr)] = prev_ordinal = ordinal

    def _parse_timetables(self, chat, yml):
        self.classes[chat] = {}

        for weekday in WEEKDAYS_RU.values():
            self.classes[chat][weekday] = []

        for section in yml.keys():
            if section in WEEKDAYS_RU.values():
                self._parse_classes(chat, yml, section)
            elif section != 'Часовой пояс' and section != 'Нумерация':
                raise SyntaxError('недопустимый раздел "%s"; обратите внимание, что дни недели должны '
                                  'быть записаны по-русски с заглавной буквы (например, "Понедельник")'
                                  % section)

    def _parse_classes(self, chat, yml, weekday):
        for time_str in yml[weekday].keys():
            time_groups = re.search(CLASS_ORDINALS_TIME_REGEX, time_str)

            if time_groups is None:
                raise SyntaxError('некорректно указано время проведения пары в день %s: "%s" — формат: "ЧЧ.мм-ЧЧ.мм"; '
                                  'обратите внимание, что задавать время как "8.00" недопустимо — нужно писать "08.00"'
                                  % (weekday, time_str))

            start_tstr = time_groups.group(1)
            end_tstr = time_groups.group(2)

            if (start_tstr, end_tstr) not in self.class_ordinals[chat]:
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

                self.classes[chat][weekday].append(ClassData(
                    start_tstr, end_tstr, class_name, host, aud, week, target_groups))


class ClassData:
    def __init__(self, start_tstr, end_tstr, name, host, aud, week, target_groups):
        self.start_tstr = start_tstr
        self.end_tstr = end_tstr
        self.name = name
        self.host = host
        self.aud = aud
        self.week = week
        self.target_groups = target_groups

    def __str__(self):
        return '%s в %s в ауд. %s (%s)' % (self.name, self.start_tstr, self.aud, self.host)


if __name__ == '__main__':
    data = urllib.request.urlopen('https://pastebin.com/raw/RhHvt6n3').read(32768)
    data = data.decode('utf-8')
    yaml.safe_load(data)
    print('ok')
    print(len(data))
