import threading
import traceback
import time
from vk_api.bot_longpoll import VkBotEventType, VkBotLongPoll

import log_util


class VKEventListener:
    def __init__(self, kristy):
        self.logger = log_util.init_logging(__name__)
        self.kristy = kristy

        threading.Thread(target=self._start, name='vk-event-listener-thread').start()

    def _start(self):
        self.logger.info('Запуск обработчика событий ВК в потоке '
                         + threading.current_thread().getName())
        try:  # добавил, чтобы теперь сервер работал всегда
            for event in self.kristy.vk_lp.listen():
                print(event)
                self._handle_event(event)
        except Exception:
            traceback.print_exc()
            self.logger.info('Крашнулся обработчик событий ВК в потоке '
                             + threading.current_thread().getName())
            self.logger.info('Жду 2 секунд до перезагрузки обработчика событий в потоке '
                             + threading.current_thread().getName())
            time.sleep(2)
            self.logger.info('Перезагрузка обработчика событий в потоке '
                             + threading.current_thread().getName())

            # FIXME тестируем
            self.kristy.vk_lp = VkBotLongPoll(self.kristy.vk_session, self.kristy.vk_group_id)
            # FIXME тестируем

            threading.Thread(target=self._start, name='vk-event-listener-thread').start()

    def _handle_event(self, event):
        if event.type == VkBotEventType.MESSAGE_NEW:
            if event.from_chat and 'action' in event.object.message \
                    and event.object.message['action']['type'] == 'chat_invite_user' \
                    and int(abs(event.object.message['action']['member_id'])) == int(self.kristy.vk_group_id):
                self._handle_new_chat(event.chat_id, event.object.message["from_id"])
            elif event.from_chat and 'action' in event.object.message \
                    and (event.object.message['action']['type'] == 'chat_invite_user'
                         or event.object.message['action']['type'] == 'chat_invite_user_by_link') \
                    and event.object.message['action']['member_id'] > 0:
                self._handle_new_member(event.chat_id, event.object.message['action']['member_id'])
            elif event.from_chat and 'action' in event.object.message and event.object.message['action']['type'] == 'chat_kick_user':
                self._handle_leave_member(event.chat_id, event.object.message['action']['member_id'])
            elif event.from_chat:
                self.kristy.vkcmdmgr.handle_chat_cmd(event)
            elif event.from_user and 'payload' in event.object.message:
                self.kristy.vkcmdmgr.handle_user_kb_cmd(event)
            elif event.from_user:
                self.kristy.vkcmdmgr.handle_user_text_cmd(event)

    def _handle_new_chat(self, chat_id, host):
        if not self.kristy.db.is_chat_in_db(chat_id):
            self.kristy.db.register_chat(chat_id, host)

        self.kristy.send(chat_id + 2E9,
                         '👋 Всем привет!\n\n'
                         'Для того, чтобы я могла вас слышать, пожалуйста, предоставьте мне доступ к переписке '
                         'в настройках беседы. Нормально общаться я смогу только с теми, кто есть в моей БД. Чтобы '
                         'туда попасть, каждому достаточно просто отправить в беседу любое сообщение. Либо можно '
                         'загрузить всех сразу — для этого дайте мне админку в беседе и используйте !загрузка\n\n'
                         '✏ А ещё попрошу дать этой беседе имя — было ли бы вам приятно, если бы вас называли '
                         '"человек 238425?". Думаю, нет ^^ Для этого используйте !название <название беседы> '
                         '(без <скобок>).')

    def _handle_new_member(self, chat_id, user_id):
        self._check_user(chat_id, user_id)
        name_chat = self.kristy.db.get_chat_name(chat_id)
        self.kristy.send(chat_id + 2E9,
                         'Добро пожаловать в болото, ой, в "{0}"'.format(name_chat))
        # self.kristy.send(chat_id + 2E9,
        #                 'Добро пожаловать. Добро пожаловать в Беседу %s. Сами вы её выбрали или её выбрали за вас, '
        #                 'это лучшая беседа из оставшихся. Я такого высокого мнения о Беседе %s, что решила разместить '
        #                 'своё расписание здесь, в Деканате, столь заботливо предоставленном нашими покровителями. '
        #                 'Я горжусь тем, что называю Беседу %s своим домом. Итак, собираетесь ли вы остаться здесь, '
        #                 'или же вас ждут неизвестные дали, добро пожаловать в Беседу %s. Здесь безопасно.'
        #                 % (chat_id, chat_id, chat_id, chat_id))
    def _handle_leave_member(self, chat_id, user_id):
        self.kristy.send(chat_id + 2E9,
                         'Мы будет скучать. А может и не будет.')
    def _check_user(self, chat_id, user_id):
        # noinspection PyBroadException
        try:
            if not self.kristy.db.chats.find_one({"chat_id": chat_id, "members": {"$eq": user_id}},
                                                 {"_id": 0, "members.$": 1}) and user_id > 0:
                self.kristy.db.add_user_to_chat(chat_id, user_id)
        except Exception:
            self.logger.error('Не удалось проверить пользователя %s в беседе № %s:', user_id, chat_id)
            traceback.print_exc()
            self.kristy.send(chat_id + 2E9, "Новый пользователь не добавлен(((")
            self.kristy.send(chat_id + 2E9, traceback.format_exc())
