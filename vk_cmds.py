import re

import groupsmgr
import timetable

# Запрещено создавать группы с этими названиями.
FORBIDDEN_NAMES = ['all', 'все', 'online', 'онлайн', 'здесь', 'here', 'тут']
# пока так, дальше будет лучше
RANK_KING = 2
RANK_ADMIN = 1
RANK_HOLOP = 0

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
        cmd.send(peer, '📚 Следующая пара: %s. До начала %s.' % (class_data, time_left))


def exec_create(cmd, chat, peer, sender, args):
    """
    !создать
    """
    existing = groupsmgr.get_all_groups(cmd.chats, chat)

    created = []
    bad_names = []
    already_existed = []

    for group in args:
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
        response += 'Я зарегистрировала эти группы: \n➕ '
        response += ' \n➕ '.join(created)

    if already_existed:
        response += 'Эти группы уже существуют: \n✔ '
        response += ' \n✔ '.join(already_existed)

    if bad_names:
        response += 'Названия этих групп недопустимы: \n🚫 '
        response += ' \n🚫 '.join(bad_names)

    cmd.send(peer, response)


def exec_delete(cmd, chat, peer, sender, args):
    """
    !удалить
    """
    deleted = []
    not_found = []
    not_creator = []

    rank_user = groupsmgr.get_rank_user(cmd.chats, chat, sender)
    existing = groupsmgr.get_all_groups(cmd.chats, chat)
    sender_created_groups = groupsmgr.get_groups_created_user(cmd.chats, chat, sender)

    for group in args:
        if group in existing:
            if group in sender_created_groups or rank_user > RANK_HOLOP:
                deleted.append(group)
                groupsmgr.delete_group(cmd.chats, chat, group)
            else:
                not_creator.append(group)
        else:
            not_found.append(group)

    if peer > 2E9:
        name_data = cmd.vk.users.get(user_id=sender)[0]
        sender_name = name_data['first_name'] + ' ' + name_data['last_name']
        response = sender_name + '\n'
    else:
        response = ''

    if deleted:
        response += 'Я удалила эти группы: \n✖ '
        response += ' \n✖ '.join(deleted)

    if not_found:
        response += 'Этих групп и так нет в беседе: \n⛔ '
        response += ' \n⛔ '.join(not_found)

    if not_creator:
        response += 'У вас нет прав, чтобы удалить эти группы: \n🚫 '
        response += ' \n🚫 '.join(not_creator)

    cmd.send(peer, response)


