import re

import groupsmgr
import kristybot
import timetable

import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.upload import VkUpload

# перемести потом куда-то запрещённые группы:
ban_groups = ["all", "все", "online", "онлайн", "здесь", "here", "тут"]

def exec_next_class(cmd, chat, peer, sender):
    """
    !пара
    """
    sender_groups = groupsmgr.get_groups(chat, sender)
    next_class = timetable.next_class(chat, sender_groups)

    if next_class is None:
        kristybot.send(peer, '🚫 На сегодня всё. Иди поспи, что ли.')
    else:
        class_data = next_class[0]
        time_left = timetable.time_left(next_class[1])
        kristybot.send(peer, '📚 Следующая пара: %s. До начала %s.' % (class_data, time_left))


def exec_create(cmd, chat, peer, sender, args):
    """
    !создать
    """
    existing = kristybot.chats.distinct("groups.name", {"chat_id": chat})

    created = []
    bad_names = []
    already_existed = []

    for group in args:
        if 2 <= len(group) <= 30 and re.match(r'[a-zA-Zа-яА-ЯёЁ0-9_]]', group) and group not in ban_groups:
            if group not in existing:
                groupsmgr.create_group(chat, group, sender)
                created.append(group)
            else:
                already_existed.append(group)
        else:
            bad_names.append(group)

    if peer > 2E9:
        name_data = kristybot.vk.users.get(user_id=sender)[0]
        sender_name = name_data['first_name'] + ' ' + name_data['last_name']
        response = sender_name + '\n'
    else:
        response = ""

    if created:
        response += '➕ Я зарегистрировала эти группы:'
        response += ('- ' + group for group in created)

    if already_existed:
        response += '✔ Эти группы уже существуют:'
        response += ('- ' + group + '\n' for group in already_existed)

    if bad_names:
        response += '🚫 Названия этих групп слишком длинные или содержат недопустимые символы:'
        response += ('- ' + group + '\n' for group in bad_names)

    kristybot.send(peer, response)
