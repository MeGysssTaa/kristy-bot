import re

import groupsmgr
import timetable

import vk_utils


# Запрещено создавать группы с этими названиями.
FORBIDDEN_NAMES = ['all', 'все', 'online', 'онлайн', 'здесь', 'here', 'тут']


def exec_next_class(cmd, chat, peer, sender):
    """
    !пара
    """
    sender_groups = groupsmgr.get_groups(cmd.chats, chat, sender)
    next_class = timetable.next_class(chat, sender_groups)

    if next_class is None:
        vk_utils.send(cmd.vk, peer, '🚫 На сегодня всё. Иди поспи, что ли.')
    else:
        class_data = next_class[0]
        time_left = timetable.time_left(next_class[1])
        vk_utils.send(cmd.vk, peer, '📚 Следующая пара: %s. До начала %s.' % (class_data, time_left))


def exec_create(cmd, chat, peer, sender, args):
    """
    !создать
    """
    print('create 1')
    existing = cmd.chats.distinct("groups.name", {"chat_id": chat})
    print('create 2')

    created = []
    bad_names = []
    already_existed = []

    print('create 3')

    for group in args:
        print('  ' + group)

        if 2 <= len(group) <= 30 and re.match(r'[a-zA-Zа-яА-ЯёЁ0-9_]', group) and group not in FORBIDDEN_NAMES:
            if group not in existing:
                print('  >> created')
                groupsmgr.create_group(chat, group, sender)
                created.append(group)
            else:
                print('  >> already exists')
                already_existed.append(group)
        else:
            print('  >> bad name')
            bad_names.append(group)

    print('create 4')

    if peer > 2E9:
        name_data = cmd.vk.users.get(user_id=sender)[0]
        sender_name = name_data['first_name'] + ' ' + name_data['last_name']
        response = sender_name + '\n'
    else:
        response = ''

    print('create 5')

    if created:
        response += '➕ Я зарегистрировала эти группы:'

        for group in created:
            response += '- ' + group + '\n'

    print('create 6')

    if already_existed:
        response += '✔ Эти группы уже существуют:'

        for group in already_existed:
            response += '- ' + group + '\n'

    print('create 7')

    if bad_names:
        response += '🚫 Названия этих групп слишком длинные или содержат недопустимые символы:'

        for group in bad_names:
            response += '- ' + group + '\n'

    print('create 8')

    vk_utils.send(cmd.vk, peer, response)

    print('create 9 END')
