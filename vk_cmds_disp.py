import json
import threading
import traceback

import pymongo
import requests
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.upload import VkUpload

import vk_cmds

class VkCmdsDispatcher(threading.Thread):
    def __init__(self, longpoll, commands):
        super(VkCmdsDispatcher, self).__init__()

        self.daemon = True
        self.longpoll = longpoll
        self.commands = commands

    def run(self):
        for event in self.longpoll.listen():
            if event.type == VkBotEventType.MESSAGE_NEW:
                if event.from_chat:
                    self.__from_chat(event)
                elif event.from_user and 'payload' in event.object.message:
                    self.__from_user_keyboard(event)
                elif event.from_user:
                    # здесь надо отправлять start_keyboard + сообщение, что юзай кнопки
                    pass

    def __from_chat(self, event):
        """
        Обработка команд в беседе.
        """
        chat = event.chat_id
        peer = event.object.message['peer_id']
        sender = event.object.message['from_id']
        msg = event.object.message['text'].strip()
        attachments = event.object.message['attachments']

        if len(msg) > 1 and msg.startswith('!'):
            # Команды
            spl = msg[1:].split(' ')
            label = spl[0].lower()
            args = spl[1:] if len(spl) > 1 else []
            target_cmd = None

            for command in self.commands:
                if not command.dm and command.label == label:
                    target_cmd = command
                    break
            if target_cmd is not None:
                # TODO (совсем потом) выполнять команды асинхронно - через пул потоков
                target_cmd.execute(chat, peer, sender, args, attachments)
        if len(msg) > 1 and msg.startswith('?'):
            # Вложения
            spl = msg[1:].split(' ')
            label = spl[0].lower()
            # TODO (совсем потом) выполнять команды асинхронно - через пул потоков
            vk_cmds.exec_use_attachment(chat, peer, label)



    def __from_user_keyboard(self, event):
        """
        Обработка команд в ЛС бота (кнопки).
        """
        payload = json.loads(event.object.message['payload'])
        sender = event.object.message['from_id']
        peer = event.object.message['peer_id']

        if 'chat_id' in payload and payload['chat_id'] == -1:
            # TODO: здесь попросить выбрать беседу в настройках (через кнопки) вместо pass
            pass
        else:
            label = payload['action']
            target_cmd = None

            for command in self.commands:
                if command.dm and command.label == label:
                    target_cmd = command
                    break

            if target_cmd is not None:
                # TODO (совсем потом) выполнять команды асинхронно - через пул потоков
                target_cmd.execute(payload['chat_id'], peer, sender, payload['args'])


class VkChatCmd:
    def __init__(self, label, desc, exec_func, min_rank=vk_cmds.Rank.WORKER, usage=None, min_args=0, dm=False, attachments=False):
        self.label = label
        self.usage = usage
        self.desc = desc
        self.min_args = min_args
        self.exec_func = exec_func
        self.dm = dm
        self.min_rank = min_rank
        self.attachments = attachments  # добавил это, потому что я хз как передавать вложения (потом надо переименовать покороче)

    def print_usage(self, peer):
        if self.usage is not None:
            self.send(peer, '⚠ Использование: \n' + self.usage)

    def print_error_rank(self, peer):
        self.send(peer, '⛔ Нет прав ⛔')

    def send(self, peer, msg, attachment=None):  # если я перенёс send в vk_cmds, то мб это убрать?
        vk_cmds.send(peer, msg, attachment)

    def execute(self, chat, peer, sender, args, attachments=False):
        # noinspection PyBroadException
        try:
            if vk_cmds.Rank[vk_cmds.groupsmgr.get_rank_user(chat, sender)].value < self.min_rank.value:  # и тут глаза Германа ушли в запой или взапой, не знаю
                self.print_error_rank(peer)
            elif len(args) < self.min_args:
                self.print_usage(peer)
            else:
                if self.min_args > 0:
                    if self.attachments:
                        self.exec_func(self, chat, peer, sender, args, attachments)
                    else:
                        self.exec_func(self, chat, peer, sender, args)
                else:
                    if self.attachments:
                        self.exec_func(self, chat, peer, sender, attachments)
                    else:
                        self.exec_func(self, chat, peer, sender)
        except Exception:
            self.send(peer, 'Ты чево наделол......\n\n' + traceback.format_exc())


def start(longpoll):
    """
    Запускает обработчик команд ВК в беседах.
    """
    commands = register_cmds()
    dispatcher = VkCmdsDispatcher(longpoll, commands)
    dispatcher.start()


def register_cmds():

    return (
        VkChatCmd(
            label='пара',
            desc='Отобразить информацию о следующей паре. Эта информация может зависеть '
                 'от того, в каких группах находится использовавший эту команду.',
            exec_func=vk_cmds.exec_next_class
        ),
        VkChatCmd(
            label='создать',
            desc='Создать новую группу.',
            usage='!создать <группа1> [группа2] [...] [группаN]',
            min_args=1,
            exec_func=vk_cmds.exec_create,
            min_rank=vk_cmds.Rank.USER
        ),
        VkChatCmd(
            label='удалить',
            desc='Удалить группу',
            usage='!удалить <группа1> [группа2] [...] [группаN]',
            min_args=1,
            exec_func=vk_cmds.exec_delete,
            min_rank=vk_cmds.Rank.MODERATOR
        ),
        VkChatCmd(
            label='подключиться',
            desc='Подключает вас к указанным группам',
            usage='!подключиться <группа1> [группа2] [...] [группаN]',
            min_args=1,
            exec_func=vk_cmds.exec_join
        ),
        VkChatCmd(
            label='отключиться',
            desc='Отключает вас от указанных групп',
            usage='!отключиться <группа1> [группа2] [...] [группаN]',
            min_args=1,
            exec_func=vk_cmds.exec_left
        ),
        VkChatCmd(
            label='подключить',
            desc='Подключает указанных людей к указанным группам',
            usage='!подключить <@юзер1> [@юзер2] [...] [@юзерN] > <группа1> [группа2] [...] [группаN]',
            min_args=3,
            exec_func=vk_cmds.exec_join_members,
            min_rank=vk_cmds.Rank.MODERATOR
        ),
        VkChatCmd(
            label='отключить',
            desc='Отключает указанных людей от указанных групп',
            usage='!отключить <@юзер1> [@юзер2] [...] [@юзерN] > <группа1> [группа2] [...] [группаN]',
            min_args=3,
            exec_func=vk_cmds.exec_left_members,
            min_rank=vk_cmds.Rank.MODERATOR
        ),
        VkChatCmd(
            label='переименовать',
            desc='Переименовывает старое название группы на новое',
            usage='!переименовать <старое_название> <новое_название>',
            min_args=2,
            exec_func=vk_cmds.exec_rename,
            min_rank=vk_cmds.Rank.MODERATOR
        ),
        VkChatCmd(
            label='неделя',
            desc='Показывает текущую неделю',
            exec_func=vk_cmds.exec_week
        ),
        VkChatCmd(
            label='рулетка',
            desc='Выбирает случайного участника беседы и выводит его фото',
            exec_func=vk_cmds.exec_roulette,
            min_rank=vk_cmds.Rank.PRO
        ),
        VkChatCmd(
            label='вложение',
            desc='Добавляет к тегу вложение, либо текст, либо и то и другое',
            usage='!вложение <режим> <тег> [текст] [вложение]',
            min_args=2,
            exec_func=vk_cmds.exec_attachment,
            min_rank=vk_cmds.Rank.PRO,
            attachments=True
        ),
        VkChatCmd(
            label='ранг',
            desc='Изменяет ранг выбранных польхователей',
            usage='!ранг <название_ранга> <@юзер1> [@юзер2] ... [@юзерN]',
            min_args=2,
            exec_func=vk_cmds.exec_change_rank,
            min_rank=vk_cmds.Rank.MODERATOR
        ),
        VkChatCmd(
            label='name',
            desc='Меняет название беседы',
            usage='!name <новое_название>',
            min_args=1,
            exec_func=vk_cmds.exec_change_name_chat,
            min_rank=vk_cmds.Rank.ADMIN
        ),
        VkChatCmd(
            label='руслан',
            desc='Руслан, просто Руслан',
            usage='!руслан',
            exec_func=vk_cmds.exec_ruslan,
            min_rank=vk_cmds.Rank.PRO
        ),
        VkChatCmd(
            label='выбор',
            desc='Выбор случайных участников беседы',
            usage='!выбор <положительное_число>',
            min_args=1,
            exec_func=vk_cmds.exec_choise,
            min_rank=vk_cmds.Rank.PRO
        ),
        VkChatCmd(
            label='ворота',
            desc='Показывает время до открытия или до закрытия ворот',
            usage='!ворота',
            exec_func=vk_cmds.exec_gate
        ),
        VkChatCmd(
            label='бфу',
            desc='Показывает всю красоту БФУ',
            usage='!бфу',
            exec_func=vk_cmds.exec_bfu
        )
    )
