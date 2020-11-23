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


def checkUser(chat_id, user_id):
    global chats
    try:
        if not chats.find_one({"chat_id": chat_id, "members": {"$eq": user_id}},
                              {"_id": 0, "members.$": 1}) and user_id > 0:
            chats.update_one({"chat_id": chat_id, "members.user_id": {"$ne": user_id}},
                             {"$push": {"members": {"user_id": user_id, "rank": "USER", "all": 0}}})
    except:
        vk.messages.send(chat_id=1, message=traceback.format_exc(), random_id=int(vk_api.utils.get_random_id()))


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
    sys.excepthook = log_uncaught_exceptions

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
