import os
import socket
import subprocess
import sys
import threading
import time
import traceback

import requests
import schedule
import vk_api
import vk_api.utils
from vk_api.bot_longpoll import VkBotLongPoll

import dbmgr
import log_util
import minigames_manager
import timetable_parser
import vkcommands
import vklistener

VERSION = '2.10.0'  # версия бота (semantics: https://semver.org/lang/ru/)

MAX_MSG_LEN = 4096
# FIXME временное решение
DIC_LETTERS = {'ь': '', 'ъ': '', 'а': 'a', 'б': 'b', 'в': 'v',
               'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo', 'ж': 'zh',
               'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l',
               'м': 'm', 'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r',
               'с': 's', 'т': 't', 'у': 'u', 'ф': 'f', 'х': 'h',
               'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch', 'ы': 'yi',
               'э': 'e', 'ю': 'yu', 'я': 'ya'}


def log_uncaught_exceptions(ex_cls, ex, tb):
    text = '{}: {}:\n'.format(ex_cls.__name__, ex)
    text += ''.join(traceback.format_tb(tb))

    print(text)

    if not os.path.isdir("../errors"):
        os.makedirs("../errors")

    with open("../errors/error_" + time.strftime("%H-%M-%S_%d%B%Y", time.localtime()) + ".txt", 'w+', encoding='utf-8') as f:
        f.write(text)

    time.sleep(30)  # ждём несколько секунд перед выходом
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
        self.lobby = {}
        self.minigames = {}
        self.db = dbmgr.DatabaseManager(self)
        self.download_chats()
        self.game_manager = minigames_manager.MinigamesManager(self)
        self.vkcmdmgr = vkcommands.VKCommandsManager(self)
        self.vklistener = vklistener.VKEventListener(self)
        self.tt_data = timetable_parser.TimetableData(self)
        self.tt_data.load_all()

        # Эти импорты обязательно должны быть локальными. Иначе будут ImportError'ы.
        import kss_executor
        import consolecmds

        self.kss_executor = kss_executor.KSSExecutor(self)
        self.console_cmds_disp = consolecmds.ConsoleCmdsDispatcher(self)

        threading.Thread(target=self._is_it_wednesday,
                         name='wednesday-frog-thread', daemon=True).start()

    # todo переместить куда-то?
    def _it_is_wednesday(self):
        self.send(2E9 + 13, "", ["photo-199300529_457265907"])

    # todo переместить куда-то?
    def _is_it_wednesday(self):
        self.logger.debug('Запуск жабы по средам в потоке '
                          + threading.current_thread().getName())

        scheduler = schedule.Scheduler()
        scheduler.every().wednesday.at('09:00').do(self._it_is_wednesday)

        while True:
            scheduler.run_pending()
            time.sleep(1)

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
        :param forward: Переслать сообщение

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
            traceback.print_exc()
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
                file_name = ""
                for i in attachment['doc']['title'].replace(' ', '_'):
                    file_name += DIC_LETTERS[i.lower()] if i.lower() in DIC_LETTERS else i
                url_doc = attachment['doc']['url']
                doc_data = requests.get(url_doc).content
                with open('../tmp/' + file_name, 'wb') as handler:  # TODO возможность одинаковых файлов, починить в будущем
                    handler.write(doc_data)
                server = self.vk.docs.get_messages_upload_server(type='doc', peer_id=peer)
                req = requests.post(server["upload_url"], files={"file": open('../tmp/' + file_name, 'rb')})
                file = req.json()
                data = self.vk.docs.save(file=file["file"], title=attachment['doc']['title'].replace(' ', '_'))
                os.remove('../tmp/' + file_name)
                array_attachments.append('doc{0}_{1}'.format(data['doc']["owner_id"], data['doc']["id"]))
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
            self.lobby.update({chat: {}})
            self.minigames.update({chat: {}})

    def check_host_lobby(self, chat, sender):
        if self.lobby[chat] and self.lobby[chat]["host"] == sender:
            return True
        else:
            return False

    def check_user_lobby(self, chat, sender):
        if self.lobby[chat] and sender in self.lobby[chat]["players"]:
            return True
        else:
            return False

if __name__ == "__main__":
    Kristy()
