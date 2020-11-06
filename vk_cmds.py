import re

import groupsmgr
import timetable


# Запрещено создавать группы с этими названиями.
FORBIDDEN_NAMES = ['all', 'все', 'online', 'онлайн', 'здесь', 'here', 'тут']


def exec_next_class(cmd, chat, peer, sender):
    """
    !пара
    """
    sender_groups = groupsmgr.get_groups(cmd.chats, chat, sender)
    next_class = timetable.next_class(chat, sender_groups)

    if next_class is None:
        cmd.send(peer, '🚫 На сегодня всё. Иди поспи, что ли.')
    else:
        class_data = next_class[0]
        time_left = timetable.time_left(next_class[1])
        cmd.send('📚 Следующая пара: %s. До начала %s.' % (class_data, time_left))


def exec_create(cmd, chat, peer, sender, args):
    """
    !создать
    """
    existing = cmd.chats.distinct("groups.name", {"chat_id": chat})

    created = []
    bad_names = []
    already_existed = []

    for group in args:
        print('  ' + group)

        if 2 <= len(group) <= 30 and re.match(r'[a-zA-Zа-яА-ЯёЁ0-9_]', group) and group not in FORBIDDEN_NAMES:
            if group not in existing:
                groupsmgr.create_group(cmd.chats, chat, group, sender)
                created.append(group)
            else:
                already_existed.append(group)
        else:
            bad_names.append(group)

    if peer > 2E9:
        name_data = cmd.vk.users.get(user_id=sender)[0]
        sender_name = name_data['first_name'] + ' ' + name_data['last_name']
        response = sender_name + '\n'
    else:
        response = ''

    if created:
        response += '➕ Я зарегистрировала эти группы:\n'

        for group in created:
            response += '- ' + group + '\n'

    if already_existed:
        response += '✔ Эти группы уже существуют:\n'

        for group in already_existed:
            response += '- ' + group + '\n'

    if bad_names:
        response += '🚫 Названия этих групп недопустимы:\n'

        for group in bad_names:
            response += '- ' + group + '\n'

    cmd.send(peer, response)
