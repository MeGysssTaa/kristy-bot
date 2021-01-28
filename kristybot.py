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
import shutil
from vk_api.bot_longpoll import VkBotLongPoll
import json

import dbmgr
import log_util
import timetable_parser
import vkcommands
import vklistener
import antony_modules

VERSION = '2.2.1'  # версия бота (semantics: https://semver.org/lang/ru/)

MAX_MSG_LEN = 4096


def log_uncaught_exceptions(ex_cls, ex, tb):
    text = '{}: {}:\n'.format(ex_cls.__name__, ex)
    text += ''.join(traceback.format_tb(tb))

    print(text)

    if not os.path.isdir("../errors"):
        os.makedirs("../errors")

    with open("../errors/error_" + time.strftime("%H-%M-%S_%d%B%Y", time.localtime()) + ".txt", 'w+', encoding='utf-8') as f:
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
        self.TIMEBAN = 2  # часы
        threading.Thread(target=self._start_socket_server,
                         name='socket-server-thread', daemon=True).start()
        self._login_vk()
        self.db = dbmgr.DatabaseManager(self)
        if os.path.isfile("../killed.txt"):
            with open("../killed.txt", "r") as killed:
                self.killed = antony_modules.dictCorrect(json.load(killed))
        else:
            self.killed = {}
        self.download_chats()
        self.vkcmdmgr = vkcommands.VKCommandsManager(self)
        self.vklistener = vklistener.VKEventListener(self)
        self.tt_data = timetable_parser.TimetableData(self)
        self.tt_data.load_all()
        if os.path.isdir("../tmp"):
            shutil.rmtree("../tmp")
        os.makedirs("../tmp")

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

        pidfile = open('../pid.txt', 'w')
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
        self.vk_lp = VkBotLongPoll(self.vk_session, self.vk_group_id)
        self.vk_upload = vk_api.upload.VkUpload(self.vk_session)
        self.vk = self.vk_session.get_api()

    def send(self, peer, msg, attachment=None, keyboard=None):
        """
        Отправляет указанное сообщение в указанный чат. Если длина сообщения превышает
        максимальную (MAX_MSG_LEN), то сообщение будет разбито на части и отправлено,
        соответственно, частями.

        :param peer: Куда отправить сообщение (peer).
        :param msg: Текст сообщения.
        :param attachment: Вложения
        :param keyboard: Клавиатура

        TODO: сделать разбиение на части более "дружелюбным" - стараться разбивать по строкам или хотя бы по пробелам.
        """
        try:
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
        except Exception:
            print("не удалось отправить сообщение ему: " + str(peer))


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
                with open('../tmp/image{0}.jpg'.format(time_now), 'wb') as handler:
                    handler.write(img_data)
                uploads = self.vk_upload.photo_messages(photos='../tmp/image{0}.jpg'.format(time_now))[0]
                os.remove('../tmp/image{0}.jpg'.format(time_now))
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
                with open('../tmp/' + file_name, 'wb') as handler:  # TODO возможность одинаковых файлов, починить в будущем
                    handler.write(doc_data)
                upload = self.vk_upload.document_message(doc='../tmp/' + file_name, peer_id=peer, title=file_name)
                os.remove('../tmp/' + file_name)
                array_attachments.append('doc{0}_{1}'.format(upload['doc']["owner_id"], upload['doc']["id"]))
            elif attachment['type'] == 'audio_message':
                url_mp3 = attachment['audio_message']['link_mp3']
                mp3_data = requests.get(url_mp3).content
                time_now = time.time()
                with open('../tmp/audio{0}.mp3'.format(time_now), 'wb') as audio:
                    audio.write(mp3_data)
                upload = self.vk_upload.audio_message(audio='../tmp/audio{0}.mp3'.format(time_now), peer_id=peer)
                os.remove('../tmp/audio{0}.mp3'.format(time_now))
                array_attachments.append('audio_message{0}_{1}'.format(upload['audio_message']["owner_id"], upload['audio_message']["id"]))
        return array_attachments

    def download_chats(self):
        chats = self.db.all_chat_ids()
        for chat in chats:
            if chat not in self.killed:
                self.killed.update({chat: {}})


if __name__ == "__main__":
    Kristy()
