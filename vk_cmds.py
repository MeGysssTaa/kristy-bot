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
    sender_groups = groupsmgr.get_user_groups(chat, sender)
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
    existing = groupsmgr.get_all_groups(chat)

    created = []
    bad_names = []
    already_existed = []

    for group in args:
        if 2 <= len(group) <= 30 and re.match(r'[a-zA-Zа-яА-ЯёЁ0-9_]', group) and group not in FORBIDDEN_NAMES:
            if group not in existing:
                groupsmgr.create_group(chat, group, sender)
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
        response += ' \n'

    if already_existed:
        response += 'Эти группы уже существуют: \n✔ '
        response += ' \n✔ '.join(already_existed)
        response += ' \n'

    if bad_names:
        response += 'Названия этих групп недопустимы: \n🚫 '
        response += ' \n🚫 '.join(bad_names)
        response += ' \n'

    cmd.send(peer, response)


def exec_delete(cmd, chat, peer, sender, args):
    """
    !удалить
    """
    deleted = []
    not_found = []
    not_creator = []

    rank_user = groupsmgr.get_rank_user(chat, sender)
    existing = groupsmgr.get_all_groups(chat)
    sender_created_groups = groupsmgr.get_groups_created_user(chat, sender)

    for group in args:
        if group in existing:
            if group in sender_created_groups or rank_user > RANK_HOLOP:
                deleted.append(group)
                groupsmgr.delete_group(chat, group)
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
        response += ' \n'

    if not_found:
        response += 'Этих групп и так нет в беседе: \n⛔ '
        response += ' \n⛔ '.join(not_found)
        response += ' \n'

    if not_creator:
        response += 'У вас нет прав, чтобы удалить эти группы: \n🚫 '
        response += ' \n🚫 '.join(not_creator)
        response += ' \n'

    cmd.send(peer, response)


def exec_join_group(cmd, chat, peer, sender, args):
    """
    !подключиться
    """
    joined = []
    already_joined = []  # переименновать
    not_found = []

    sender_groups = groupsmgr.get_user_groups(chat, sender)
    existing = groupsmgr.get_all_groups(chat)

    for group in args:
        if group in existing:
            if group not in sender_groups:
                joined.append(group)
                groupsmgr.join_group(chat, group, sender)
            else:
                already_joined.append(group)
        else:
            not_found.append(group)

    if peer > 2E9:
        name_data = cmd.vk.users.get(user_id=sender)[0]
        sender_name = name_data['first_name'] + ' ' + name_data['last_name']
        response = sender_name + '\n'
    else:
        response = ''

    if joined:
        response += 'Добавила вас в эти группы: \n➕ '
        response += ' \n➕ '.join(joined)
        response += ' \n'

    if already_joined:
        response += 'Вы уже состоите в этих группах: \n✔ '
        response += ' \n✔ '.join(already_joined)
        response += ' \n'

    if not_found:
        response += 'Эти группы я не нашла: \n🚫 '
        response += ' \n🚫 '.join(not_found)
        response += ' \n'

    cmd.send(peer, response)


def exec_left_group(cmd, chat, peer, sender, args):
    """
    !отключиться
    """
    left = []
    already_left = []
    not_found = []

    sender_groups = groupsmgr.get_user_groups(chat, sender)
    existing = groupsmgr.get_all_groups(chat)

    for group in args:
        if group in existing:
            if group in sender_groups:
                left.append(group)
                groupsmgr.left_group(chat, group, sender)
            else:
                already_left.append(group)
        else:
            not_found.append(group)

    if peer > 2E9:
        name_data = cmd.vk.users.get(user_id=sender)[0]
        sender_name = name_data['first_name'] + ' ' + name_data['last_name']
        response = sender_name + '\n'
    else:
        response = ''

    if left:
        response += 'Успешно отключила вас от групп: \n✖ '
        response += ' \n✖ '.join(left)
        response += ' \n'

    if already_left:
        response += 'Вас и не было в этих группах: \n⛔ '
        response += ' \n⛔ '.join(already_left)
        response += ' \n'

    if not_found:
        response += 'Эти группы я не нашла: \n🚫 '
        response += ' \n🚫 '.join(not_found)
        response += ' \n'

    cmd.send(peer, response)


def exec_join_member_group(cmd, chat, peer, sender, args):
    """
    !подключить
    """
    rank_sender = groupsmgr.get_rank_user(chat, sender)
    if rank_sender == RANK_HOLOP:
        cmd.send(peer, "У вас нет прав")
        return
    if '>' not in args or args.count('>') > 1:
        cmd.print_usage(peer)
        return
    users = list(filter(re.compile(r'\[id+(\d+)\|\W*\w+\]').match, args[:args.index('>')]))
    groups = list(filter(re.compile(
        r'[a-zA-Zа-яА-ЯёЁ0-9_]').match,
                         args[args.index('>') + 1:] if len(args.count) - 1 > args.index('>') else []))
    if not users or not groups:
        cmd.print_usage(peer)
        return

    users = [int(user) for user in users]
    existing_groups = groupsmgr.get_all_groups(chat)
    existing_users = groupsmgr.get_all_users(chat)

    not_found = []
    joined = {}
    for user in users:
        if user in existing_users:
            joined.update({user: []})
            sender_groups = groupsmgr.get_user_groups(chat, user)
            for group in groups:
                if group in existing_groups and group not in sender_groups:
                    groupsmgr.join_group(chat, group, user)
                    joined[user].append(group)
            if not joined[user]:
                del joined[user]
        else:
            not_found.append(user)

    all_users_vk = cmd.vk.users.get(user_ids=users)
    first_names_joined = ""
    first_names_not_found = ""
    for user_vk in all_users_vk: # хрен его знает, мб потом переделаем
        if user_vk["id"] in joined:
            first_names_joined += "{0} > {1} \n".format("[id{0}|{1}]".format(str(user_vk["id"]), user_vk["first_name"]),
                                                     ' '.join(joined[user_vk["id"]]))
        if user_vk["id"] in not_found:
            first_names_not_found += "[id{0}|{1}] \n".format(str(user_vk["id"]), user_vk["first_name"])

    if peer > 2E9:
        name_data = cmd.vk.users.get(user_id=sender)[0]
        sender_name = name_data['first_name'] + ' ' + name_data['last_name']
        response = sender_name + '\n'
    else:
        response = ''

    if first_names_joined:
        response += first_names_joined

    if first_names_not_found:
        response += 'Данных пользователей нет в базе данных: \n' + first_names_not_found

    if not first_names_not_found and not first_names_joined:
        response += 'Никто никуда не добавлен'

    cmd.send(peer, response)

