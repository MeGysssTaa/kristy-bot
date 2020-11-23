import os
import re
import socket
import sys
import threading
import time
import traceback

import pymongo
import requests
import schedule
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.upload import VkUpload

import consolecmds
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
    keyboard = VkKeyboard()
    chat = -1

    keyboard.add_button("Почта",
                        payload={"action": "почта_выбор", "chat_id": chat},
                        color=VkKeyboardColor.PRIMARY
                        )
    keyboard.add_line()
    keyboard.add_button("Подключиться",
                        payload={"action": "подключиться_выбор", "chat_id": chat, "args": []},
                        color=VkKeyboardColor.POSITIVE
                        )
    keyboard.add_button("Отключиться",
                        payload={"action": "отключиться_выбор", "chat_id": chat, "args": []},
                        color=VkKeyboardColor.NEGATIVE
                        )
    keyboard.add_line()
    keyboard.add_button("Все группы",
                        payload={"action": "все_группы", "chat_id": chat}
                        )
    keyboard.add_button("Мои группы",
                        payload={"action": "мои_группы", "chat_id": chat}
                        )
    keyboard.add_button("Состав",
                        payload={"action": "состав_группы", "chat_id": chat, "args": []}
                        )
    keyboard.add_line()
    keyboard.add_button("Развлечение",
                        payload={"action": "развлечение", "chat_id": chat}
                        )
    keyboard.add_button("Настройки",
                        payload={"action": "настройки_выбор", "chat_id": chat}
                        )
    return keyboard


def createSelectChatKeyboard(payload, user_id):
    chats_user = list(chats.aggregate([{"$match": {"$and": [{"members.user_id": user_id}]}}, {
        "$group": {"_id": "1", "chats": {"$push": {"chat_id": "$chat_id", "name": "$name"}}}},
                                       {"$sort": {"chat_id": 1}}]))
    if chats_user:
        keyboard = VkKeyboard(one_time=True)
        for chat in chats_user[0]["chats"]:
            payload["chat_id"] = chat["chat_id"]
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
        else:
            try:
                attachmentslist.append(attachment["type"] + str(attachment[attachment["type"]]["owner_id"]) + '_' + str(
                    attachment[attachment["type"]]["id"]))
            except:
                traceback.print_exc()
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

    threading.Thread(target=vk_cmds_disp.vk_cmds.__start_classes_notifier, daemon=True).start()
    # timetable_parser#load_all вызывается при импорте vk_cmds прямо оттуда
    # vk_cmds#

    # FIXME consolecmds.start()
    vk_cmds_disp.start(vklong)

    for event in vklong.listen():
        if event.type == VkBotEventType.MESSAGE_NEW and event.from_chat and 'action' in event.object.message and \
                event.object.message['action']['type'] == 'chat_invite_user' and int(
            abs(event.object.message['action']['member_id'])) == int(group_id):
            vk.messages.send(chat_id=1, message="Бот добавлен в группу: " + str(event.chat_id),
                             random_id=int(vk_api.utils.get_random_id()))
            if not chats.find_one({"chat_id": event.chat_id}):
                chats.insert_one({"chat_id": event.chat_id, "name": str(event.chat_id),
                                  "members": [{"user_id": event.object.message["from_id"], "rank": "KING", "all": 0}],
                                  "groups": [], "attachments": [], "email": []})
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





            # проверка пингов с +
            if re.findall(r"(?:\s|^)\@([a-zA-Zа-яА-ЯёЁ0-9_]+)\+(?=\s|$)", event.object.message["text"]):
                pinglist = []
                for ping in re.findall(r"(?:\s|^)\@([a-zA-Zа-яА-ЯёЁ0-9_]+)(?=\s|$)", event.object.message["text"].lower()):
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


