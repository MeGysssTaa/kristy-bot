import re

import groupsmgr
import timetable


# перемести потом куда-то запрещённые группы:
ban_groups = ["all", "все", "online", "онлайн", "здесь", "here", "тут"]


def exec_next_class(cmd, chat, peer, sender):
    """
    !пара
    """
    print('next_class1')

    from vk_utils import send
    print('next_class2')

    sender_groups = groupsmgr.get_groups(cmd.chats, chat, sender)
    print('next_class3')
    next_class = timetable.next_class(chat, sender_groups)
    print('next_class4')

    if next_class is None:
        print('next_classA5')
        send(peer, '🚫 На сегодня всё. Иди поспи, что ли.')
        print('next_classA6')
    else:
        print('next_classB5')
        class_data = next_class[0]
        print('next_classB6')
        time_left = timetable.time_left(next_class[1])
        print('next_classB7')
        send(peer, '📚 Следующая пара: %s. До начала %s.' % (class_data, time_left))
        print('next_classB8')

    print('next_classEND')


def exec_create(cmd, chat, peer, sender, args):
    """
    !создать
    """
    from kristybot import send, chats, vk
    existing = chats.distinct("groups.name", {"chat_id": chat})

    created = []
    bad_names = []
    already_existed = []

    for group in args:
        if 2 <= len(group) <= 30 and re.match(r'[a-zA-Zа-яА-ЯёЁ0-9_]', group) and group not in ban_groups:
            if group not in existing:
                groupsmgr.create_group(chat, group, sender)
                created.append(group)
            else:
                already_existed.append(group)
        else:
            bad_names.append(group)

    if peer > 2E9:
        name_data = vk.users.get(user_id=sender)[0]
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

    send(peer, response)
