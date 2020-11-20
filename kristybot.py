import json
import os
import random
import re
import socket
import sys
import threading
import time
import traceback

import pymongo
import requests
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.upload import VkUpload

import consolecmds
import timetable
import vk_cmds_disp

MAX_MSG_LEN = 4096


def log_uncaught_exceptions(ex_cls, ex, tb):
    global sock
    text = '{}: {}:\n'.format(ex_cls.__name__, ex)
    text += ''.join(traceback.format_tb(tb))
    print(text)
    sock.close()
    if not os.path.isdir(os.path.dirname(__file__) + os.path.sep + "errors"):
        os.makedirs(os.path.dirname(__file__) + os.path.sep + "errors")
    with open(os.path.dirname(__file__) + os.path.sep + "errors" + os.path.sep + "error_" + time.strftime(
            "%H-%M-%S_%d%B%Y", time.localtime()) + ".txt", 'w+', encoding='utf-8') as f:
        f.write(text)


def server():
    """
    Это для того, чтобы знать, почему бот говно. Короче нужна.
    """
    global port_server, sock
    try:
        sock = socket.socket()
        sock.bind(('', port_server))
        sock.listen(1)
        while True:
            conn, addr = sock.accept()
            conn.close()
    except:
        time.sleep(3)
        sock.close()
        server()


def downloads():
    global tokentext, group_id, host, port, version, port_server
    sys.excepthook = log_uncaught_exceptions
    pid = str(os.getpid())
    pidfile = open(os.path.dirname(__file__) + os.path.sep + 'pid.txt', 'w')
    pidfile.write(pid)
    pidfile.close()


    group_id = int(os.environ['VKGROUP_ID'])

    port_server = int(os.environ['VKBOT_UPTIMEROBOT_PORT'])


def sendmessage(message):
    try:
        while (len(message) > 0):
            vk.messages.send(chat_id=1, message=message[0:4000] + version, random_id=int(vk_api.utils.get_random_id()))
            message.replace(message[0:4000], "")
    except:
        vk.messages.send(chat_id=1, message=traceback.print_exc(), random_id=int(vk_api.utils.get_random_id()))


def checkUser(chat_id, user_id):
    global chats
    try:
        if not chats.find_one({"chat_id": chat_id, "members": {"$eq": user_id}},
                              {"_id": 0, "members.$": 1}) and user_id > 0:
            chats.update_one({"chat_id": chat_id, "members.user_id": {"$ne": user_id}},
                             {"$push": {"members": {"user_id": user_id, "rank": "USER", "all": 0}}})
    except:
        vk.messages.send(chat_id=1, message=traceback.format_exc(), random_id=int(vk_api.utils.get_random_id()))


def createStartKeyboard():
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button("Все группы", color=VkKeyboardColor.SECONDARY, payload={"action": "groups_all", "chat_id": -1})
    keyboard.add_button("Мои группы", color=VkKeyboardColor.SECONDARY, payload={"action": "groups_my", "chat_id": -1})
    keyboard.add_button("Прогулять?", color=VkKeyboardColor.SECONDARY, payload={"action": "go_to_para"})
    return keyboard


def createSelectChatKeyboard(payload, user_id):
    chats_user = list(chats.aggregate([{"$match": {"$and": [{"members.user_id": user_id}]}}, {
        "$group": {"_id": "1", "chats": {"$push": {"chat_id": "$chat_id", "name": "$name"}}}},
                                       {"$sort": {"chat_id": 1}}]))
    if chats_user:
        keyboard = VkKeyboard(one_time=True)
        for chat in chats_user[0]["chats"]:
            payload["chat_id"] = chat["chat_id"]
            if "name" not in chat:
                chat.update({"name": chat["chat_id"]})
            if "name" in chat and chat["name"] == "":
                chat["name"] = chat["chat_id"]
            keyboard.add_button(chat["name"], color=VkKeyboardColor.SECONDARY, payload=payload)
            if (list(chats_user[0]["chats"]).index(chat) + 1) % 3 == 0 and list(chats_user[0]["chats"]).index(
                    chat) != 0:
                keyboard.add_line()
        keyboard.add_button("НАЗАД", color=VkKeyboardColor.NEGATIVE, payload={"action": "exit_select_chats"})
        return keyboard
    return createStartKeyboard()


def sendMessageToUsers(user_ids, message, attachments):
    global vk, upload
    attachmentslist = []
    for attachment in attachments:
        if attachment["type"] == "photo":
            try:
                for photo in attachment[attachment["type"]]["sizes"]:
                    if photo["type"] == 'w':
                        img_data = requests.get(photo["url"]).content
                        with open(os.path.dirname(__file__) + os.path.sep + 'image.jpg', 'wb') as handler:
                            handler.write(img_data)
                        uploads = upload.photo_messages(photos=os.path.dirname(__file__) + os.path.sep + 'image.jpg')[0]
                        attachmentslist.append('photo{}_{}'.format(uploads["owner_id"], uploads["id"]))
            except:
                traceback.print_exc()
                print("что-то пошло не так")
        elif attachment["type"] == "wall":
            try:
                attachmentslist.append(attachment["type"] + str(attachment[attachment["type"]]["from_id"]) + '_' + str(
                    attachment[attachment["type"]]["id"]))
            except:
                traceback.print_exc()
                print(1)
        else:
            try:
                print(attachment)
                attachmentslist.append(attachment["type"] + str(attachment[attachment["type"]]["owner_id"]) + '_' + str(
                    attachment[attachment["type"]]["id"]))
            except:
                traceback.print_exc()
                print(1)
    print(attachmentslist)
    for user_id in user_ids:
        try:
            vk.messages.send(user_id=user_id, message=message, attachment=','.join(attachmentslist),
                             random_id=int(vk_api.utils.get_random_id()))
        except:
            traceback.print_exc()
            print("не получилось")


def log_txt(ex_cls, ex, tb):
    with open('error.txt', 'w', encoding='utf-8') as f:
        text = '{}: {}:\n'.format(ex_cls.__name__, ex)
        text += ''.join(traceback.format_tb(tb))
        f.write(text)
    quit()


def GetChatsDB():
    host = os.environ['MONGO_HOST']
    port = int(os.environ['MONGO_PORT'])

    client = pymongo.MongoClient(host, port)
    db = client.kristybot
    chats = db.chats

    return chats

def GetVkSession():
    tokentext = os.environ['VKGROUP_TOKEN']
    return vk_api.VkApi(token=tokentext)

if __name__ == "__main__":
    sys.excepthook = log_txt

    downloads()
    chats = GetChatsDB()

    vk_session = vk_cmds_disp.vk_cmds.vk_session  # просто блять до связи
    vk = vk_cmds_disp.vk_cmds.vk  # хы хы
    vklong = VkBotLongPoll(vk_session, group_id)
    upload = VkUpload(vk_session)

    serverporok = threading.Thread(target=server, daemon=True)
    serverporok.start()

    # FIXME consolecmds.start()

    timetable.load()
    # FIXME threading.Thread(target=timetable.start_classes_notifier, daemon=True).start()

    vk_cmds_disp.start(vklong)
    for event in vklong.listen():
        if event.type == VkBotEventType.MESSAGE_NEW and event.from_chat and 'action' in event.object.message and \
                event.object.message['action']['type'] == 'chat_invite_user' and int(
            abs(event.object.message['action']['member_id'])) == int(group_id):
            vk.messages.send(chat_id=1, message="Бот добавлен в группу: " + str(event.chat_id),
                             random_id=int(vk_api.utils.get_random_id()))
            if not chats.find_one({"chat_id": event.chat_id}):
                chats.insert_one({"chat_id": event.chat_id, "name": "",
                                  "members": [{"user_id": event.object.message["from_id"], "rank": 2, "all": 0}],
                                  "groups": [], "attachments": []})
                vk.messages.send(chat_id=event.chat_id,
                                 message="Приветик, рада всех видеть! в беседе №{}\n".format(str(event.chat_id)) +
                                         "Для того, чтобы мы смогли общаться -> предоставьте мне доступ ко всей переписке \n"
                                         "Я здесь новенькая, поэтому моя база данных о каждом из вас пуста((( \n"
                                         "Чтобы познакомиться со мной и я смогла узнать о вас лучше -> напишите любое сообщение в чат \n"
                                         "Или вы можете дать мне права администратора, после чего прописать команду !download, тем самым загрузив всех пользователей одновременно! \n"
                                         "Также попрошу короля назначить имя этой беседы, через !name <имя>, которое будет использоваться в рассылках.",
                                 random_id=int(vk_api.utils.get_random_id()))
        elif event.type == VkBotEventType.MESSAGE_NEW and event.from_chat and 'action' in event.object.message and (
                event.object.message['action']['type'] == 'chat_invite_user' or event.object.message['action'][
            'type'] == 'chat_invite_user_by_link') and event.object.message['action']['member_id'] > 0:
            try:
                checkUser(event.chat_id, event.object.message['action']['member_id'])
                vk.messages.send(chat_id=event.chat_id, message="Добро пожаловать в нашу беседу)))",
                                 random_id=int(vk_api.utils.get_random_id()))
            except:
                vk.messages.send(chat_id=event.chat_id, message="Новый пользователь не добавлен(((",
                                 random_id=int(vk_api.utils.get_random_id()))
        elif event.type == VkBotEventType.MESSAGE_NEW and event.from_chat:
            checkUser(event.chat_id, event.object.message["from_id"])
            if re.findall(r'^!(\w+)', event.object.message["text"]) and not re.findall(r"\[club+(\d+)\|\W*\w+\]",
                                                                                       event.object.message["text"]):
                event.object.message["text"] = event.object.message["text"].lower()  # тестируем
                command = re.findall(r'^!(\w+)', event.object.message["text"])[0]
                # Команды, которые только с админкой


                if command == "бфу":
                    vk.messages.send(chat_id=event.chat_id, attachment="photo-199300529_457239023",
                                     random_id=int(vk_api.utils.get_random_id()))
                elif command == "аня":
                    vk.messages.send(chat_id=event.chat_id, attachment="photo-199300529_457239031",
                                     random_id=int(vk_api.utils.get_random_id()))
                elif command == "пиздец":
                    vk.messages.send(chat_id=event.chat_id, attachment="photo-199300529_457239032",
                                     random_id=int(vk_api.utils.get_random_id()))
                elif command == "похуй":
                    vk.messages.send(chat_id=event.chat_id, attachment="photo-199300529_457239033",
                                     random_id=int(vk_api.utils.get_random_id()))
                elif command == "бабенко":
                    vk.messages.send(chat_id=event.chat_id, attachment="photo-199300529_457239034",
                                     random_id=int(vk_api.utils.get_random_id()))
                elif command == "жопа":
                    vk.messages.send(chat_id=event.chat_id, attachment="photo-199300529_457239100",
                                     random_id=int(vk_api.utils.get_random_id()))
                elif command == "ворота":
                    today_time = (time.gmtime().tm_hour + 2) * 3600 + time.gmtime().tm_min * 60 + time.gmtime().tm_sec
                    vorota_time = 0
                    if today_time < 28800:
                        vorota_time = 28800 - today_time
                    elif 32400 < today_time < 46800:
                        vorota_time = 46800 - today_time
                    elif 50400 < today_time < 61200:
                        vorota_time = 61200 - today_time
                    elif 66600 < today_time:
                        vorota_time = 86400 - today_time + 28800
                    if vorota_time:
                        time_do_vorot = timetable.time_left_ru(
                            int(vorota_time / 3600),
                            int(vorota_time % 3600 / 60),
                            int(vorota_time % 3600 % 60)
                        )
                        vk.messages.send(chat_id=event.chat_id, message="Ворота закрыты. До открытия " + time_do_vorot,
                                         random_id=int(vk_api.utils.get_random_id()))
                    else:
                        vk.messages.send(chat_id=event.chat_id, message="Ворота открыты",
                                         random_id=int(vk_api.utils.get_random_id()))
                elif command == "семён":
                    vk.messages.send(chat_id=event.chat_id, attachment="photo-199300529_457239151",
                                     random_id=int(vk_api.utils.get_random_id()))
                elif command == "дистант":
                    vk.messages.send(chat_id=event.chat_id, attachment="photo-199300529_457239154",
                                     random_id=int(vk_api.utils.get_random_id()))
                elif command == "окей":
                    vk.messages.send(chat_id=event.chat_id, message="мы просто играем в жизнь",
                                     random_id=int(vk_api.utils.get_random_id()))
                elif command == "флекс":
                    vk.messages.send(chat_id=event.chat_id, attachment="photo-199300529_457239168",
                                     random_id=int(vk_api.utils.get_random_id()))
                elif command == "гурьевск":
                    vk.messages.send(chat_id=event.chat_id, attachment="audio233737645_456239192",
                                     random_id=int(vk_api.utils.get_random_id()))
                elif command == "python":
                    vk.messages.send(chat_id=event.chat_id, attachment="photo-199300529_457239218",
                                     random_id=int(vk_api.utils.get_random_id()))
                elif command == "экзамен":
                    vk.messages.send(chat_id=event.chat_id, message="ну давай, попробуй сдать экзамен",
                                     attachment="photo-199300529_457239228",
                                     random_id=int(vk_api.utils.get_random_id()))
                elif command == "лопиталь":
                    vk.messages.send(chat_id=event.chat_id, attachment="photo-199300529_457239229",
                                     random_id=int(vk_api.utils.get_random_id()))



            # проверка пингов без +
            if re.findall(r"(?:\s|^)\@([a-zA-Zа-яА-ЯёЁ\d]+)(?=\s|$)", event.object.message["text"]):
                pinglist = []
                for ping in re.findall(r"\@(\w+)", event.object.message["text"].lower()):
                    user_ids = chats.find_one(
                        {"chat_id": event.chat_id, "groups": {"$elemMatch": {"name": {"$eq": ping}}}},
                        {"_id": 0, "groups.members.$": 1})
                    if user_ids:
                        for user_id in user_ids["groups"][0]["members"]:
                            if user_id not in pinglist and user_id != event.object.message["from_id"]:
                                pinglist.append(user_id)
                pinger = vk.users.get(user_id=event.object.message["from_id"])[0]
                pinger_text = pinger["first_name"] + " " + pinger["last_name"] + " пинганул: \n"
                domains_list = []
                if pinglist:
                    domains_list = vk.users.get(user_ids=list(pinglist), fields=["domain"])
                domains_dict = {}
                for domain in domains_list:
                    domains_dict.update({str(domain["id"]): domain["domain"]})
                if domains_dict:
                    vk.messages.send(chat_id=event.chat_id, message=pinger_text + "☝☝☝☝☝☝☝☝☝☝ \n@" + ' @'.join(
                        list(domains_dict.values())) + " \n☝☝☝☝☝☝☝☝☝☝ ", random_id=int(vk_api.utils.get_random_id()))
            # проверка пингов с +
            if re.findall(r"(?:\s|^)\@([a-zA-Zа-яА-ЯёЁ\d]+)\+(?=\s|$)", event.object.message["text"]):
                pinglist = []
                for ping in re.findall(r"\@(\w+)", event.object.message["text"].lower()):
                    user_ids = chats.find_one(
                        {"chat_id": event.chat_id, "groups": {"$elemMatch": {"name": {"$eq": ping}}}},
                        {"_id": 0, "groups.members.$": 1})
                    if user_ids:
                        for user_id in user_ids["groups"][0]["members"]:
                            if user_id not in pinglist:
                                pinglist.append(user_id)
                if pinglist:
                    user = vk.users.get(user_id=event.object.message["from_id"])
                    name_user = user[0]["first_name"] + ' ' + user[0]["last_name"]
                    name = chats.find_one({"chat_id": event.chat_id}, {"_id": 0, "name": 1})
                    if not name["name"]:
                        name["name"] = str(event.chat_id)
                    sendmessages = threading.Thread(target=sendMessageToUsers,
                                                    args=(pinglist, "Отправлено из беседы: " + name["name"]
                                                          + " \nКем: " + name_user
                                                          + ' \nСообщение: ' + event.object.message["text"],
                                                          event.object.message["attachments"],))
                    sendmessages.start()
            # подсчёт all
            if re.findall(r"\@all(?=\s|$)", event.object.message["text"]):
                try:  # на всякий
                    imposter = vk.users.get(user_id=event.object.message["from_id"])[0]
                    imposter_text = imposter["first_name"] + " " + imposter["last_name"]
                    chats.update_one({"chat_id": event.chat_id, "members.user_id": event.object.message["from_id"]},
                                     {"$inc": {"members.$.all": 1}})
                    # vk.messages.send(chat_id=event.chat_id, message=imposter_text +", 😡", random_id=int(vk_api.utils.get_random_id()))
                except:
                    print(1)

        elif event.type == VkBotEventType.MESSAGE_NEW and event.from_user:
            try:
                if "payload" in event.object.message:
                    event.object.message["payload"] = json.loads(event.object.message["payload"])
                    if "chat_id" in event.object.message["payload"] and event.object.message["payload"][
                        "chat_id"] == -1:
                        vk.messages.send(user_id=event.object.message["from_id"], message="Выберите беседу",
                                         random_id=int(vk_api.utils.get_random_id()),
                                         keyboard=createSelectChatKeyboard(event.object.message["payload"],
                                                                           event.object.message[
                                                                               "from_id"]).get_keyboard())
                        continue
                    if event.object.message["payload"]["action"] == "groups_all":
                        try:
                            groups_all = chats.distinct("groups.name",
                                                        {"chat_id": event.object.message["payload"]["chat_id"],
                                                         "members.user_id": event.object.message["from_id"]})
                            if groups_all:
                                groups_all_text = "Все группы: \n"
                                for number in range(1, len(groups_all) + 1):
                                    groups_all_text += str(number) + ". " + groups_all[number - 1] + " \n"
                                vk.messages.send(user_id=event.object.message["from_id"], message=groups_all_text,
                                                 random_id=int(vk_api.utils.get_random_id()),
                                                 keyboard=createStartKeyboard().get_keyboard())
                            else:
                                vk.messages.send(user_id=event.object.message["from_id"],
                                                 message="Не найденно групп в беседе",
                                                 random_id=int(vk_api.utils.get_random_id()),
                                                 keyboard=createStartKeyboard().get_keyboard())
                        except Exception as ex:
                            traceback.print_exc()
                            vk.messages.send(user_id=event.object.message["from_id"], message="Что-то пошло не так(((",
                                             random_id=int(vk_api.utils.get_random_id()),
                                             keyboard=createStartKeyboard().get_keyboard())
                    elif event.object.message["payload"]["action"] == "groups_my":
                        groups_my_all = list(chats.aggregate([{"$unwind": "$groups"}, {"$match": {
                            "$and": [{"chat_id": event.object.message["payload"]["chat_id"]},
                                     {"groups.members": {"$eq": event.object.message["from_id"]}}]}}, {
                                                                  "$group": {"_id": "$chat_id",
                                                                             "groups": {"$push": "$groups.name"}}}]))
                        if groups_my_all:
                            groups_my_text = "Группы, в которых вы есть: \n"
                            for number in range(1, len(groups_my_all[0]["groups"]) + 1):
                                groups_my_text += str(number) + ". " + groups_my_all[0]["groups"][number - 1] + " \n"
                            vk.messages.send(user_id=event.object.message["from_id"], message=groups_my_text,
                                             random_id=int(vk_api.utils.get_random_id()),
                                             keyboard=createStartKeyboard().get_keyboard())
                        else:
                            vk.messages.send(user_id=event.object.message["from_id"],
                                             message="Вас нет в группах этой беседы",
                                             random_id=int(vk_api.utils.get_random_id()),
                                             keyboard=createStartKeyboard().get_keyboard())
                    elif event.object.message["payload"]["action"] == "go_to_para":
                        chance = int(vk_api.utils.get_random_id())
                        if chance % 100 == 0 and random.SystemRandom().random.randint(1, 2) == 1:
                            chance = 0
                        elif chance % 100 == 0 and random.SystemRandom().random.randint(1, 2) == 2:
                            chance = 100
                        else:
                            chance %= 100
                        vk.messages.send(user_id=event.object.message["from_id"],
                                         message="Рекомендую прогулять пару с вероятностью: " + str(chance) + "%",
                                         random_id=int(vk_api.utils.get_random_id()),
                                         keyboard=createStartKeyboard().get_keyboard())
                    elif event.object.message["payload"]["action"] == "exit_select_chats":
                        vk.messages.send(user_id=event.object.message["from_id"], message="Я вернула вас в меню выбора",
                                         random_id=int(vk_api.utils.get_random_id()),
                                         keyboard=createStartKeyboard().get_keyboard())

                elif re.findall(r'^!(\w+)', event.object.message["text"]) and not re.findall(r"\[club+(\d+)\|\W*\w+\]",
                                                                                             event.object.message[
                                                                                                 "text"]):
                    event.object.message["text"] = event.object.message["text"].lower()  # тестируем
                    command = re.findall(r'^!(\w+)', event.object.message["text"])[0]
                    if command == "помощь":
                        vk.messages.send(user_id=event.object.message["from_id"],
                                         message="Команды: \n!моигруппы <номер_чата> - выводит группы, в которых вы состоите в выбраном чате \n"
                                                 "!всегруппы <номер_чата> - выводит все группы беседы",
                                         keyboard=createStartKeyboard().get_keyboard(),
                                         random_id=int(vk_api.utils.get_random_id()))
                    if command == "моигруппы":
                        try:
                            groups_my_all = list(chats.aggregate([{"$unwind": "$groups"}, {"$match": {
                                "$and": [{"chat_id": int(event.object.message["text"].split()[1])},
                                         {"groups.members": {"$eq": event.object.message["from_id"]}}]}}, {
                                                                      "$group": {"_id": "$chat_id", "groups": {
                                                                          "$push": "$groups.name"}}}]))
                            if groups_my_all:
                                groups_my_text = "Группы, в которых вы есть: \n"
                                for number in range(1, len(groups_my_all[0]["groups"]) + 1):
                                    groups_my_text += str(number) + ". " + groups_my_all[0]["groups"][
                                        number - 1] + " \n"
                                vk.messages.send(user_id=event.object.message["from_id"], message=groups_my_text,
                                                 random_id=int(vk_api.utils.get_random_id()),
                                                 keyboard=createStartKeyboard().get_keyboard())
                            else:
                                vk.messages.send(user_id=event.object.message["from_id"],
                                                 message="Вас нет в группах этой беседы",
                                                 random_id=int(vk_api.utils.get_random_id()),
                                                 keyboard=createStartKeyboard().get_keyboard())
                        except Exception as ex:
                            traceback.print_exc()
                            vk.messages.send(user_id=event.object.message["from_id"], message="Что-то пошло не так(((",
                                             random_id=int(vk_api.utils.get_random_id()))
                    elif command == "всегруппы":
                        try:
                            groups_all = chats.distinct("groups.name",
                                                        {"chat_id": int(event.object.message["text"].split()[1]),
                                                         "members.user_id": event.object.message["from_id"]})
                            groups_all_text = "Все группы: \n"
                            for number in range(1, len(groups_all) + 1):
                                groups_all_text += str(number) + ". " + groups_all[number - 1] + " \n"
                            vk.messages.send(user_id=event.object.message["from_id"], message=groups_all_text,
                                             random_id=int(vk_api.utils.get_random_id()),
                                             keyboard=createStartKeyboard().get_keyboard())
                        except Exception as ex:
                            traceback.print_exc()
                            vk.messages.send(user_id=event.object.message["from_id"], message="Что-то пошло не так(((",
                                             random_id=int(vk_api.utils.get_random_id()),
                                             keyboard=createStartKeyboard().get_keyboard())

                else:
                    vk.messages.send(user_id=event.object.message["from_id"],
                                     message="Используйте клавиши снизу, либо напишите !помощь",
                                     random_id=int(vk_api.utils.get_random_id()),
                                     keyboard=createStartKeyboard().get_keyboard())
            except:
                vk.messages.send(user_id=event.object.message["from_id"], message="Что-то пошло не так(((",
                                 random_id=int(vk_api.utils.get_random_id()))
