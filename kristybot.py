import socket
import subprocess
import sys
import threading
import time
import traceback
import os

import vk_api
import vk_api.utils
from vk_api.bot_longpoll import VkBotLongPoll

import dbmgr
import log_util
import timetable_parser

import vkcommands
import vklistener


MAX_MSG_LEN = 4096


def log_uncaught_exceptions(ex_cls, ex, tb):
    text = '{}: {}:\n'.format(ex_cls.__name__, ex)
    text += ''.join(traceback.format_tb(tb))

    print(text)

    if not os.path.isdir(os.path.dirname(__file__) + os.path.sep + "errors"):
        os.makedirs(os.path.dirname(__file__) + os.path.sep + "errors")

    with open(os.path.dirname(__file__) + os.path.sep + "errors" + os.path.sep + "error_"
              + time.strftime("%H-%M-%S_%d%B%Y", time.localtime()) + ".txt", 'w+', encoding='utf-8') as f:
        f.write(text)

    time.sleep(5)  # ждём несколько секунд перед выходом
    exit(1)


class Kristy:
    def __init__(self):
        sys.excepthook = log_uncaught_exceptions

        self.logger = log_util.init_logging(__name__)
        self._fetch_version()
        self._fetch_pid()
        self.logger.info('Запуск! Версия: %s, ID процесса: %s', self.version, self.pid)

        threading.Thread(target=self._start_socket_server,
                         name='socket-server-thread', daemon=True).start()

        self._login_vk()
        self.db = dbmgr.DatabaseManager(self)
        self.vkcmdmgr = vkcommands.VKCommandsManager(self)
        self.vklistener = vklistener.VKEventListener(self)
        self.tt_data = timetable_parser.TimetableData(self)
        self.tt_data.load_all()

    def _fetch_version(self):
        with subprocess.Popen(['git', 'rev-parse', 'HEAD'], shell=False, stdout=subprocess.PIPE) as process:
            # Получаем объект типа bytes (последовательность байт).
            # Конвертируем эту последовательность в строку - получаем что-то вроде b'xxxxxxxxxx...'
            # Нам нужны первые 7 символов из ID коммита. Опускаем первые 2 символа ("b" и кавычку "'")
            # и получаем интервал [2:9] (индекс 2 включаем, индекс 9 - нет). Префикс 'git-' для ясности.
            git_commit_id_bytes = process.communicate()[0].strip()
            self.version = 'git-' + str(git_commit_id_bytes)[2:9]

    def _fetch_pid(self):
        self.pid = str(os.getpid())

        pidfile = open('pid.txt', 'w')
        pidfile.write(self.pid)
        pidfile.close()

    def _start_socket_server(self):
        """
        Сервер-пустышка для UptimeRobot'а.
        """
        # noinspection PyBroadException
        try:
            self.server = socket.socket()
            self.server.bind(('', int(os.environ['VKBOT_UPTIMEROBOT_PORT'])))
            self.server.listen(1)

            while True:
                conn, addr = self.server.accept()
                conn.close()
        except Exception:
            # Перезапуск через 3 секунды.
            time.sleep(3)
            self.server.close()
            self._start_socket_server()

    def _login_vk(self):
        self.vk_group_id = os.environ['VKGROUP_ID']
        self.vk_session = vk_api.VkApi(token=os.environ['VKGROUP_TOKEN'])
        self.vk_upload = vk_api.upload.VkUpload(self.vk_session)
        self.vk_lp = VkBotLongPoll(self.vk_session, self.vk_group_id)
        self.vk = self.vk_session.get_api()

    def send(self, peer, msg, attachment=None, keyboard=None):
        """
        Отправляет указанное сообщение в указанный чат. Если длина сообщения превышает
        максимальную (MAX_MSG_LEN), то сообщение будет разбито на части и отправлено,
        соответственно, частями.

        :param peer: Куда отправить сообщение (peer_id).
        :param msg: Текст сообщения.
        :param attachment: Вложения
        :param keyboard: Клавиатура

        TODO: сделать разбиение на части более "дружелюбным" - стараться разбивать по строкам или хотя бы по пробелам.
        """
        if len(msg) <= MAX_MSG_LEN:
            self.vk.messages.send(peer_id=peer,
                                  message=msg,
                                  attachment=attachment,
                                  keyboard=keyboard,
                                  random_id=int(vk_api.utils.get_random_id()))
        else:
            # TODO ... (вложения, кнопки(?) в последний кусок сообщения)
            chunks = (msg[k:k + MAX_MSG_LEN] for k in range(0, len(msg), MAX_MSG_LEN))

            for chunk in chunks:
                self.vk.messages.send(peer_id=peer,
                                      message=chunk,
                                      random_id=int(vk_api.utils.get_random_id()))


if __name__ == "__main__":
    Kristy()
