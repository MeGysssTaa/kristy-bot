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
        for event in self.longpoll:
            if event.type == VkBotEventType.MESSAGE_NEW:
                if event.from_chat:
                    self.__from_chat(event)
                elif event.from_user and"payload" in event.object.message:
                    self.__from_user(event)

    def __from_chat(self, event):
        chat = event.chat_id
        sender = event.object.message["from_id"]
        msg = event.object.message["text"].strip()

        if len(msg) > 1 and msg.startswith('!'):
            spl = msg[1:].split(' ')
            label = spl[0].lower()
            args = spl[1:] if len(spl) > 1 else []
            target_cmd = None

            for command in self.commands:
                if command.label == label:
                    target_cmd = command
                    break

            if target_cmd is not None:
                # TODO: выполнять команды асинхронно - через пул потоков
                target_cmd.execute(chat, sender, args)

    def __from_user(self, event):
        payload = json.loads(event.object.message["payload"])

        if "chat_id" in event.object.message["payload"] and event.object.message["payload"]["chat_id"] == -1:
            kristybot.send(user_id=event.object.message["from_id"], message="Выберите беседу",
                             random_id=int(vk_api.utils.get_random_id()),
                             keyboard=createSelectChatKeyboard(event.object.message["payload"],
                                                               event.object.message["from_id"]).get_keyboard())
            return


class VkChatCmd:
    def __init__(self, label, desc, exec_func, usage=None, min_args=0):
        self.label = label
        self.usage = usage
        self.desc = desc
        self.min_args = min_args
        self.exec_func = exec_func

    def print_usage(self, target_chat):
        if self.usage is not None:
            kristybot.send(target_chat, '⚠ Использование: ' + self.usage)

    def execute(self, chat, sender, args):
        if len(args) < self.min_args:
            self.print_usage(chat)
        else:
            # noinspection PyBroadException
            try:
                if len(args) > 0:
                    self.exec_func(self, chat, sender, args)
                else:
                    self.exec_func(self, chat, sender)
            except Exception:
                kristybot.send(chat, 'Ты чево наделол......\n\n' + traceback.format_exc())


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
            desc='Отображает информацию о следующей паре. Эта информация может зависеть от того, '
                 'в каких группах находится использовавший эту команду.',
            exec_func=vk_cmds.exec_para
        )
    )
