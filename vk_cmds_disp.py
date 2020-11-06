import json
import threading
import traceback

import pymongo
import requests
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.upload import VkUpload

import kristybot
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
                    self.__from_user(event)
                elif event.from_user:
                    # здесь надо отправлять start_keyboard
                    pass

    def __from_chat(self, event):
        """
        Обработка команд в беседе.
        """
        chat = event.chat_id
        peer = event.object.message['peer_id']
        sender = event.object.message['from_id']
        msg = event.object.message['text'].strip()

        if len(msg) > 1 and msg.startswith('!'):
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
                target_cmd.execute(chat, peer, sender, args, None)

    def __from_user(self, event):
        """
        Обработка команд в ЛС бота (кнопки).
        """
        payload = json.loads(event.object.message['payload'])
        sender = event.object.message['from_id']
        peer = event.object.message['peer_id']

        if 'chat_id' in payload and payload['chat_id'] == -1:
            # TODO: здесь попросить выбрать беседу (через кнопки) вместо pass
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
                target_cmd.execute(payload['chat_id'], peer, sender, None, payload)


class VkChatCmd:
    def __init__(self, label, desc, exec_func, usage=None, min_args=0, dm=False):
        self.label = label
        self.usage = usage
        self.desc = desc
        self.min_args = min_args
        self.exec_func = exec_func
        self.dm = dm

    def print_usage(self, peer):
        if self.usage is not None:
            kristybot.send(peer, '⚠ Использование: ' + self.usage)

    def execute(self, chat, peer, sender, args, payload):
        # noinspection PyBroadException
        try:
            if self.dm:
                self.exec_func(self, chat, peer, sender, payload)
            else:
                if len(args) < self.min_args:
                    self.print_usage(peer)
                else:
                    if len(args) > 0:
                        self.exec_func(self, chat, peer, sender, args)
                    else:
                        self.exec_func(self, chat, peer, sender)
        except Exception:
            kristybot.send(peer, 'Ты чево наделол......\n\n' + traceback.format_exc())


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
            usage='создать <группа1> <группа2> [...] <группаN>',
            min_args=1,
            exec_func=vk_cmds.exec_create
        )
    )
