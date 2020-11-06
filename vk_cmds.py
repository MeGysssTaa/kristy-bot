import groupsmgr
import kristybot
import timetable

import pymongo
import requests
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.upload import VkUpload


def exec_para(cmd, chat, sender):
    """
    !пара
    """
    sender_groups = groupsmgr.get_groups(kristybot.chats, chat, sender)
    next_class = timetable.next_class(chat, sender_groups)

    if next_class is None:
        kristybot.vk.messages.send(chat_id=chat,
                                   message="🚫 На сегодня всё. Иди поспи, что ли.",
                                   random_id=int(vk_api.utils.get_random_id()))
    else:
        class_data = next_class[0]
        time_left = timetable.time_left(next_class[1])
        kristybot.vk.messages.send(chat_id=chat,
                                   message="📚 Следующая пара: %s. До начала %s." % (class_data, time_left),
                                   random_id=int(vk_api.utils.get_random_id()))
