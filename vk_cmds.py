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

def exec_create():
    """
    !создать
    """
    groups_off = []
    groups_on = []
    if not re.findall(r"(?<=\s)[a-zA-Zа-яА-ЯёЁ\d]+(?=\s|$)", event.object.message["text"]):
        vk.messages.send(chat_id=event.chat_id,
                         message="Вы не ввели группы, либо использовали недопустимые символы в названиях",
                         random_id=int(vk_api.utils.get_random_id()))
        continue
    groups_find = list(set(re.findall(r"(?<=\s)[a-zA-Zа-яА-ЯёЁ\d]+(?=\s|$)", event.object.message["text"])) - set(
        ["all", "все", "online", "онлайн"]))
    groups_off = list(set(groups_find) - set(chats.distinct("groups.name", {"chat_id": event.chat_id})))
    groups_on = list(set(groups_find) - set(groups_off))
    groups_off.sort()
    groups_on.sort()

    name_vk = vk.users.get(user_id=event.object.message["from_id"])
    name = name_vk[0]["first_name"] + " " + name_vk[0]["last_name"]
    for group in groups_off:
        chats.update_one({"chat_id": event.chat_id}, {"$push": {
            "groups": {"name": group, "creator": event.object.message["from_id"], "members": [], "kicked": [],
                       "info": ""}}})
    if not groups_on and groups_off:
        test = vk.messages.send(chat_id=event.chat_id,
                                message=name + "\nЯ добавила все ниже перечисленные группы:\n➕ " + '\n➕ '.join(
                                    groups_off), random_id=int(vk_api.utils.get_random_id()))
    else:
        if not groups_off:
            vk.messages.send(chat_id=event.chat_id,
                             message=name + "\nВсе группы и так уже добавлены:\n✔ " + '\n✔ '.join(groups_on),
                             random_id=int(vk_api.utils.get_random_id()))
        else:
            vk.messages.send(chat_id=event.chat_id,
                             message=name + "\nЯ добавила все нижеперечисленные группы:\n➕ " + '\n➕ '.join(groups_off)
                                     + "\nНо также некоторые группы уже были добавлены ранее:\n✔ " + '\n✔ '.join(
                                 groups_on), random_id=int(vk_api.utils.get_random_id()))
