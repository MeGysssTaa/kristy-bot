import re
from enum import Enum, auto
import groupsmgr
import timetable
import vk_api
import os
import time, datetime
from kristybot import GetVkSession

vk_session = GetVkSession()
vk = vk_session.get_api()

# Запрещено создавать группы с этими названиями.
FORBIDDEN_NAMES = ['all', 'все', 'online', 'онлайн', 'здесь', 'here', 'тут']
MAX_MSG_LEN = 4096


class Rank(Enum):
    """
    Описание рангов:
    GOVNO     - Не может использовать бота, мне жалко этого человека будет
    WORKER    - Может подключаться и отключаться от групп, также просматривать все группы, свои группы и участников
                группы, может использовать префикс вложений бота, может просматривать ранги участников беседы,
                может использовать расписание и всё с ним связанное
    USER      - Может тегать по группам, может делать рассылки, а также добавлять сообщения в почту беседы
    PRO       - Может добавлять новые вложения в группе, может делать случайный выбор
                нескольких людей или играть в русскую рулетку
    MODERATOR - Может подключать и отключать участников от групп, а также удалять группы, которые не создавал, переименовывать группы,
                может менять ранги других
    ADMIN     - По сути это как король, только король 1, админов может быть несколько
    KING      - Абсолютная власть над чатом
    """
    GOVNO = auto()
    WORKER = auto()
    USER = auto()
    PRO = auto()
    MODERATOR = auto()
    ADMIN = auto()
    KING = auto()


def send(peer, msg, attachment=None):
    """
    Отправляет указанное сообщение в указанный чат. Если длина сообщения превышает
    максимальную (MAX_MSG_LEN), то сообщение будет разбито на части и отправлено,
    соответственно, частями.

    :param peer: Куда отправить сообщение (peer_id).
    :param msg: Текст сообщения.
    :param attachment: Вложения

    TODO: сделать разбиение на части более "дружелюбным" - стараться разбивать по строкам или хотя бы по пробелам.
    """
    if len(msg) <= MAX_MSG_LEN:
        vk.messages.send(peer_id=peer, message=msg, attachment=attachment, random_id=int(vk_api.utils.get_random_id()))
    else:
        chunks = (msg[k:k + MAX_MSG_LEN] for k in range(0, len(msg), MAX_MSG_LEN))

        for chunk in chunks:
            vk.messages.send(peer_id=peer, message=chunk, random_id=int(vk_api.utils.get_random_id()))


def exec_next_class(cmd, chat, peer, sender):
    """
    !пара
    """
    sender_groups = groupsmgr.get_user_groups(chat, sender)
    next_class = timetable.next_class(chat, sender_groups)

    if next_class is None:
        send(peer, '🚫 На сегодня всё. Иди поспи, что ли.')
    else:
        class_data = next_class[0]
        time_left = timetable.time_left(next_class[1])
        time_left_str = 'До начала ' + time_left + '.' if time_left is not None else 'Занятие вот-вот начнётся!'
        send(peer, '📚 Следующая пара: %s. %s' % (class_data, time_left_str))


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
        name_data = vk.users.get(user_id=sender)[0]
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

    send(peer, response)


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
            if group in sender_created_groups or Rank[rank_user].value >= Rank.MODERATOR.value:
                deleted.append(group)
                groupsmgr.delete_group(chat, group)
            else:
                not_creator.append(group)
        else:
            not_found.append(group)

    if peer > 2E9:
        name_data = vk.users.get(user_id=sender)[0]
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

    send(peer, response)


def exec_join(cmd, chat, peer, sender, args):
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
        name_data = vk.users.get(user_id=sender)[0]
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

    send(peer, response)


def exec_left(cmd, chat, peer, sender, args):
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
        name_data = vk.users.get(user_id=sender)[0]
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

    send(peer, response)


def exec_join_members(cmd, chat, peer, sender, args):
    """
    !подключить
    """
    if '>' not in args or args.count('>') > 1:
        cmd.print_usage(peer)
        return
    users = re.findall(r'\[id+(\d+)\|\W*\w+\]', ' '.join(args[:args.index('>')]))
    groups = list(filter(re.compile(
        r'[a-zA-Zа-яА-ЯёЁ0-9_]').match,
                         args[args.index('>') + 1:] if len(args) - 1 > args.index('>') else []))
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

    all_users_vk = vk.users.get(user_ids=users)
    first_names_joined = ""
    first_names_not_found = ""
    for user_vk in all_users_vk:  # хрен его знает, мб потом переделаем
        if user_vk["id"] in joined:
            first_names_joined += "{0} > {1} \n".format("[id{0}|{1}]".format(str(user_vk["id"]), user_vk["first_name"]),
                                                        ' '.join(joined[user_vk["id"]]))
        if user_vk["id"] in not_found:
            first_names_not_found += "[id{0}|{1}] \n".format(str(user_vk["id"]), user_vk["first_name"])

    if peer > 2E9:
        name_data = vk.users.get(user_id=sender)[0]
        sender_name = name_data['first_name'] + ' ' + name_data['last_name']
        response = sender_name + '\n'
    else:
        response = ''

    if first_names_joined:
        response += 'Добавила: \n'
        response += first_names_joined

    if first_names_not_found:
        response += 'Данных пользователей нет в базе данных: \n'
        response += first_names_not_found

    if not first_names_not_found and not first_names_joined:
        response += 'Никто никуда не добавлен'

    send(peer, response)


def exec_left_members(cmd, chat, peer, sender, args):
    """
    !отключить
    """
    if '>' not in args or args.count('>') > 1:
        cmd.print_usage(peer)
        return
    users = re.findall(r'\[id+(\d+)\|\W*\w+\]', ' '.join(args[:args.index('>')]))
    groups = list(filter(re.compile(
        r'[a-zA-Zа-яА-ЯёЁ0-9_]').match,
                         args[args.index('>') + 1:] if len(args) - 1 > args.index('>') else []))
    if not users or not groups:
        cmd.print_usage(peer)
        return

    users = [int(user) for user in users]
    existing_groups = groupsmgr.get_all_groups(chat)
    existing_users = groupsmgr.get_all_users(chat)

    not_found = []
    left = {}
    for user in users:
        if user in existing_users:
            left.update({user: []})
            sender_groups = groupsmgr.get_user_groups(chat, user)
            for group in groups:
                if group in existing_groups and group in sender_groups:
                    groupsmgr.left_group(chat, group, user)
                    left[user].append(group)
            if not left[user]:
                del left[user]
        else:
            not_found.append(user)

    all_users_vk = vk.users.get(user_ids=users)
    first_names_left = ""
    first_names_not_found = ""
    for user_vk in all_users_vk:  # хрен его знает, мб потом переделаем
        if user_vk["id"] in left:
            first_names_left += "{0} > {1} \n".format("[id{0}|{1}]".format(str(user_vk["id"]), user_vk["first_name"]),
                                                      ' '.join(left[user_vk["id"]]))
        if user_vk["id"] in not_found:
            first_names_not_found += "[id{0}|{1}] \n".format(str(user_vk["id"]), user_vk["first_name"])

    if peer > 2E9:
        name_data = vk.users.get(user_id=sender)[0]
        sender_name = name_data['first_name'] + ' ' + name_data['last_name']
        response = sender_name + '\n'
    else:
        response = ''

    if first_names_left:
        response += 'Отключила: \n'
        response += first_names_left

    if first_names_not_found:
        response += 'Данных пользователей нет в базе данных: \n'
        response += first_names_not_found

    if not first_names_not_found and not first_names_left:
        response += 'Никого не отключила'

    send(peer, response)


def exec_rename(cmd, chat, peer, sender, args):
    """
    !переименовать
    """
    name_old = args[0]
    name_new = args[1]

    if name_new in FORBIDDEN_NAMES or len(name_new) < 2 or len(name_new) > 30 or not re.match(r'[a-zA-Zа-яА-ЯёЁ0-9_]',
                                                                                              name_new):
        send(peer, "Новое название группы является недопустимым: " + name_new)
        return

    existing = groupsmgr.get_all_groups(chat)

    if name_old not in existing:
        send(peer, "Такой группы нет в базе данных: " + name_old)
        return
    if name_new in existing:
        send(peer, "Такая группа уже есть в базе данных: " + name_new)
        return

    groupsmgr.rename_group(chat, name_old, name_new)

    if peer > 2E9:
        name_data = vk.users.get(user_id=sender)[0]
        sender_name = name_data['first_name'] + ' ' + name_data['last_name']
        response = sender_name + '\n'
    else:
        response = ''

    response += 'Успешно установила новое название группы: ' + name_new
    send(peer, response)


def exec_change_rank(cmd, chat, peer, sender, args):
    """
    Команда, для изменения ранга
    TODO Антоша обязательно сделает, у него в голове норм идея
    """
    change_to_this_rank = args[0]  # название переделать FIX PLS
    sender_rank = groupsmgr.get_rank_user(chat, sender)
    if change_to_this_rank not in Rank.__members__:
        send(peer, 'Не найден такой ранг')
        return
    if Rank[sender_rank].value < Rank[change_to_this_rank].value:
        send(peer, 'У вас нет прав на этот ранг')
        return
    users = re.findall(r'\[id+(\d+)\|\W*\w+\]', ' '.join(args[1:]))
    users_up = []
    users_down = []
    users_eq = []
    users_error = []
    existing_users = groupsmgr.get_all_users(chat)
    users = [int(user) for user in users]

    for user in users:
        if user in existing_users:
            user_rank = groupsmgr.get_rank_user(chat, user)
            if Rank[change_to_this_rank].value > Rank[user_rank].value:
                groupsmgr.change_rank(chat, user, change_to_this_rank)
                users_up.append(user)
            elif Rank[change_to_this_rank].value < Rank[user_rank].value < Rank[sender_rank].value:
                groupsmgr.change_rank(chat, user, change_to_this_rank)
                users_down.append(user)
            else:
                users_eq.append(user)
        else:
            users_error.append(user)
    all_users_vk = vk.users.get(user_ids=users)
    if peer > 2E9:
        name_data = vk.users.get(user_id=sender)[0]
        sender_name = name_data['first_name'] + ' ' + name_data['last_name']
        response = sender_name + '\n'
    else:
        response = ''
    # дальше можно описать одним словом: помогите
    if users_up:
        response += "Повышены в ранге до {0}: \n".format(change_to_this_rank)
        for user in users_up:
            for user_vk in all_users_vk:  # да бред, потом чё-нибудь придумаю
                if user == user_vk["id"]:
                    response += "🔼 [id{0}|{1}] \n".format(user_vk["id"], user_vk["first_name"])

    if users_down:
        response += "Понижены в ранге до {0}: \n".format(change_to_this_rank)
        for user in users_down:
            for user_vk in all_users_vk:  # да бред, потом чё-нибудь придумаю
                if user == user_vk["id"]:
                    response += "🔽 [id{0}|{1}] \n".format(user_vk["id"], user_vk["first_name"])

    if users_eq:
        response += "Ранг не изменён: \n"
        for user in users_eq:
            for user_vk in all_users_vk:  # да бред, потом чё-нибудь придумаю
                if user == user_vk["id"]:
                    response += "▶ [id{0}|{1}] \n".format(user_vk["id"], user_vk["first_name"])

    if users_error:
        response += "Пользователи не найдёны: \n"
        for user in users_error:
            for user_vk in all_users_vk:  # да бред, потом чё-нибудь придумаю
                if user == user_vk["id"]:
                    response += "❌ [id{0}|{1}] \n".format(user_vk["id"], user_vk["first_name"])
        pass

    send(peer, response)


def exec_week(cmd, chat, peer, sender):
    """
    !неделя
    """
    send(peer, str("Сейчас " + timetable.get_week() + " неделя").upper())


def exec_roulette(cmd, chat, peer, sender):
    response = "Играем в русскую рулетку. И проиграл у нас: "
    users = groupsmgr.get_all_users(chat)
    random_user = users[vk_api.utils.get_random_id() % len(users)]
    user_photo = vk.users.get(user_id=random_user, fields=["photo_id"])[0]["photo_id"]
    send(peer, response, "photo" + user_photo)


def exec_use_attachment(chat, peer, tag):
    """
    ? - отправляет вложения + текст
    """
    attachment = groupsmgr.get_attachment(chat, tag)
    if attachment:
        send(peer, attachment["message"], attachment["attachments"])


def exec_add_attachment(cmd, chat, peer, sender, args, attachments):
    """
    !вложение - добавляет вложение к тегу
    """
    tag = args[0]
    message = args[1:] if args > 1 else []
    if not message and not attachments:
        cmd.print_usage(peer)
        return
    groupsmgr.add_attachment(chat, tag, message, attachments)


def exec_change_name_chat(cmd, chat, peer, sender, args):
    """
    системная команда
    !name - меняет название беседы
    """
    new_name = args[0]
    if new_name in groupsmgr.get_names_chats():
        send(peer, "Данное имя используется")
        return
    groupsmgr.change_name_chat(chat, new_name)
    send(peer, "Успешно обновила имя беседы")


def exec_ruslan(cmd, chat, peer, sender):
    """
    !руслан - просто Руслан (шар судьбы)
    """
    answers = ["Беспорно", "Предрешено", "Никаких сомнений", "Определённо да", "Можешь быть уверен в этом",
               "Мне кажется - «да»", "Вероятнее всего", "Хорошие перспективы", "Знаки говорят - «да»", "Да",
               "Пока не ясно, попробуй снова", "Спроси позже", "Лучше не рассказывать", "Сейчас нельзя предсказать", "Сконцентрируйся и спроси опять",
               "Даже не думай", "Мой ответ — «нет»", "По моим данным — «нет»", "Перспективы не очень хорошие", "Весьма сомнительно"]
    final_answer = answers[os.urandom(1)[0] % 20]
    send(peer, final_answer)


def exec_choise(cmd, chat, peer, sender, args):
    """
    !выбор - выбирает случайных участников беседы
    """
    number = args[0]

    if not str(number).isdigit() or not int(number) > 0:
        cmd.print_usage(peer)
        return

    response = "Случайно были выбраны: \n"

    users = groupsmgr.get_all_users(chat)
    count = len(users) - int(number)

    for i in range(count):
        users.remove(users[os.urandom(1)[0] % len(users)])
    users_vk = vk.users.get(user_ids=users)
    for number, user in enumerate(users_vk):
        response += str(number + 1) + ". " + user["first_name"] + " " + user[
            "last_name"] + " \n"
    send(peer, response)


def exec_gate(cmd, chat, peer, sender):  # пока так, дальше посмотрим
    """
    !ворота
    """
    format_time = '%H:%S'
    timezone = 2 * 60 * 60  # +2 часа
    time_open_gate = [
        ['08:30', '09:00'],
        ['13:00', '14:00'],
        ['17:00', '18:30']
    ]
    time_open_gate.sort()
    time_now_struct = time.gmtime(time.time() + timezone)
    time_now = time_now_struct.tm_hour * 3600 + time_now_struct.tm_min * 60 + time_now_struct.tm_sec

    for number, time_gate in enumerate(time_open_gate):
        # я искал легче путь, но я обожаю время ☻
        time_start_now = time.strptime(time_gate[0], format_time).tm_hour * 60 * 60 + time.strptime(time_gate[0], format_time).tm_min * 60
        time_end_now = time.strptime(time_gate[1], format_time).tm_hour * 60 * 60 + time.strptime(time_gate[1], format_time).tm_min * 60
        time_start_next = time.strptime(time_open_gate[(number + 1) % len(time_open_gate)][0], format_time).tm_hour * 60 * 60 + time.strptime(time_open_gate[(number + 1) % len(time_open_gate)][0], format_time).tm_min * 60
        if time_start_now <= time_now <= time_end_now:
            response = "Ворота открыты. До закрытия "
            time_closing = time_end_now - time_now
            response += timetable.time_left_ru(
                time_closing // 60 * 60,
                time_closing % (60 * 60) // 60,
                time_closing % (60 * 60) % 60
            )
            send(peer, response)
            return
        elif time_end_now < time_now < time_start_next:
            response = "Ворота закрыты. До открытия "
            time_opening = time_start_next - time_now
            response += timetable.time_left_ru(
                time_opening // (60 * 60),
                time_opening % (60 * 60) // 60,
                time_opening % (60 * 60) % 60
            )
            send(peer, response)
            return
        elif (number + 1) == len(time_open_gate) and (time_end_now < time_now or time_now < time_start_next):
            response = "Ворота закрыты. До открытия "
            time_opening = (time_start_next - time_now) if time_start_next > time_now else (24 * 60 * 60 - time_now + time_start_next)
            response += timetable.time_left_ru(
                time_opening // (60 * 60),
                time_opening % (60 * 60) // 60,
                time_opening % (60 * 60) % 60
            )
            send(peer, response)
            return
    send(peer, "Нету времени")
