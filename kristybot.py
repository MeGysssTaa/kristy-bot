import socket
import subprocess
import sys
import threading
import time
import traceback
import os
import requests
import vk_api
import vk_api.utils
from vk_api.bot_longpoll import VkBotLongPoll

import dbmgr
import log_util
import timetable_parser

import vkcommands
import vklistener

VERSION = '3.0.1'  # версия бота (semantics: https://semver.org/lang/ru/)

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

        self.chat_stats = {}
        threading.Thread(target=self._thread_stats,
                         name='socket-server-thread', daemon=True).start()

    def _fetch_version(self):
        with subprocess.Popen(['git', 'rev-parse', 'HEAD'], shell=False, stdout=subprocess.PIPE) as process:
            # Получаем объект типа bytes (последовательность байт).
            # Конвертируем эту последовательность в строку - получаем что-то вроде b'xxxxxxxxxx...'
            # Нам нужны первые 7 символов из ID коммита. Опускаем первые 2 символа ("b" и кавычку "'")
            # и получаем интервал [2:9] (индекс 2 включаем, индекс 9 - нет). Префикс 'git-' для ясности.
            # К результату слева добавляем версию бота в человекочитаемом формате (semantics).
            git_commit_id_bytes = process.communicate()[0].strip()
            self.version = VERSION + '-git-' + str(git_commit_id_bytes)[2:9]

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

    def _thread_stats(self):
        for peer in self.chat_stats:
            stat = self.chat_stats[peer]
            messages = sorted(stat["messages"].items(), key=lambda x: x[1], reverse=True)[0]
            print(str(messages[1]))
            voices = sorted(stat["voices"].items(), key=lambda x: x[1], reverse=True)[0] if stat["voices"] else []
            alls = sorted(stat["alls"].items(), key=lambda x: x[1], reverse=True)[0] if stat["alls"] else []
            attachments = sorted(stat["attachments"].items(), key=lambda x: x[1], reverse=True)[0] if stat["attachments"] else []
            response = '📈 Статистика на сегодня: \n'
            name_data = self.vk.users.get(user_id=messages[0])[0]
            sender_name = name_data['first_name'] + ' ' + name_data['last_name']
            response += '🙃 Больше всего сообщений: %s (%s) \n' % (sender_name, str(messages[1]))
            if voices:
                name_data = self.vk.users.get(user_id=voices[0])[0]
                sender_name = name_data['first_name'] + ' ' + name_data['last_name']
                response += '😈 Больше всего голосовых: %s (%s) \n' % (sender_name, (str(voices[1])))
            else:
                response += '✖ Сегодня без голосовых (как-то тихо) \n'

            if alls:
                name_data = self.vk.users.get(user_id=alls[0])[0]
                sender_name = name_data['first_name'] + ' ' + name_data['last_name']
                response += '😡 Больше всего all: %s (%s) \n' % (sender_name, (str(alls[1])))
            else:
                response += '✖ Сегодня без all (ура) \n'

            if attachments:
                name_data = self.vk.users.get(user_id=attachments[0])[0]
                sender_name = name_data['first_name'] + ' ' + name_data['last_name']
                response += '😎 Больше всего вложений: %s (%s) \n' % (sender_name, (str(attachments[1])))
            else:
                response += '✖ Сегодня без вложений (я что, зря создавал эту функцию?) \n'
            self.send(peer, response)
        self.chat_stats.clear()
        if int(time.time() + 2 * 60 * 60) % 86400 < 84600:
            time.sleep(84600 - int(time.time() + 2 * 60 * 60) % 86400)
        else:
            time.sleep(171000 - int(time.time() + 2 * 60 * 60) % 86400)
        self._thread_stats()

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

    def get_list_attachments(self, attachments, peer):
        """
        Преобразует attachments ВКашный в нормальный, чтобы можно было обращаться через send
        """
        array_attachments = []
        for attachment in list(attachments):
            if attachment['type'] == 'photo':
                max_photo_url = ""
                max_width = 0
                for photo in attachment['photo']['sizes']:
                    if max_width < photo['width']:
                        max_width = photo['width']
                        max_photo_url = photo['url']
                img_data = requests.get(max_photo_url).content
                time_now = time.time()
                with open('image{0}.jpg'.format(time_now), 'wb') as handler:
                    handler.write(img_data)
                uploads = self.vk_upload.photo_messages(photos='image{0}.jpg'.format(time_now))[0]
                os.remove('image{0}.jpg'.format(time_now))
                array_attachments.append('photo{0}_{1}'.format(uploads["owner_id"], uploads["id"]))
            elif attachment['type'] == 'video':
                array_attachments.append('video{0}_{1}_{2}'.format(attachment['video']['owner_id'], attachment['video']['id'], attachment['video']['access_key']))
            elif attachment['type'] == 'audio':
                array_attachments.append('audio{0}_{1}'.format(attachment['audio']['owner_id'], attachment['audio']["id"]))
            elif attachment['type'] == 'wall':
                if not attachment['wall']['from']['is_closed']:
                    array_attachments.append('wall{0}_{1}'.format(attachment['wall']['to_id'], attachment['wall']['id']))
            elif attachment['type'] == 'doc':
                file_name = attachment['doc']['title']
                url_doc = attachment['doc']['url']
                doc_data = requests.get(url_doc).content
                with open(file_name, 'wb') as handler:  # TODO возможность одинаковых файлов, почтинить в будущем
                    handler.write(doc_data)
                upload = self.vk_upload.document_message(doc=file_name, peer_id=peer, title=file_name)
                os.remove(file_name)
                array_attachments.append('doc{0}_{1}'.format(upload['doc']["owner_id"], upload['doc']["id"]))
        return array_attachments


if __name__ == "__main__":
    Kristy()
