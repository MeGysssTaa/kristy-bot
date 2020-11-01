import os
import re
import time
import traceback
import threading
import requests
import json
import random
import socket
import sys

import pymongo
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.upload import VkUpload
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
def log_uncaught_exceptions(ex_cls, ex, tb):
    global sock
    text = '{}: {}:\n'.format(ex_cls.__name__, ex)
    text += ''.join(traceback.format_tb(tb))
    print(text)
    sock.close()
    if not os.path.isdir(os.path.dirname(__file__) + os.path.sep + "errors"):
        os.makedirs(os.path.dirname(__file__) + os.path.sep + "errors")
    with open(os.path.dirname(__file__) + os.path.sep + "errors" + os.path.sep + "error_" + time.strftime("%H-%M-%S_%d%B%Y", time.localtime()) + ".txt", 'w+', encoding='utf-8') as f:
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
    pidfile = open(os.path.dirname(__file__) + os.path.sep + 'pid.txt', 'w')
    pidfile.write(str(os.getpid()))
    pidfile.close()

    tokentext = os.environ['VKGROUP_TOKEN']
    group_id = int(os.environ['VKGROUP_ID'])
    host = os.environ['MONGO_HOST']
    port = int(os.environ['MONGO_PORT'])
    port_server = int(os.environ['VKBOT_UPTIMEROBOT_PORT'])

def sendmessage(message):
    try:
        while(len(message) > 0):
            vk.messages.send(chat_id=1, message = message[0:4000] + version, random_id=int(vk_api.utils.get_random_id()))
            message.replace(message[0:4000], "")
    except:
        vk.messages.send(chat_id=1, message = traceback.print_exc(), random_id=int(vk_api.utils.get_random_id()))


def checkUser(chat_id, user_id):
    global chats
    try:
        if not chats.find_one({"chat_id": chat_id, "members": {"$eq": user_id}}, {"_id": 0, "members.$": 1}) and user_id > 0:
            chats.update_one({"chat_id": chat_id, "members.user_id": {"$ne": user_id}}, {"$push": {"members": {"user_id": user_id, "rank": 0, "all": 0}}})
    except:
        vk.messages.send(chat_id=1, message=traceback.format_exc(), random_id=int(vk_api.utils.get_random_id()))

def createStartKeyboard():
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button("Все группы", color=VkKeyboardColor.SECONDARY, payload={"action": "groups_all", "chat_id": -1})
    keyboard.add_button("Мои группы", color=VkKeyboardColor.SECONDARY, payload={"action": "groups_my", "chat_id": -1})
    keyboard.add_button("Прогулять?", color=VkKeyboardColor.SECONDARY, payload={"action": "go_to_para"})
    return keyboard
def createSelectChatKeyboard(payload, user_id):
    chats_user = list(chats.aggregate([{"$match": {"$and": [{"members.user_id": user_id}]}}, {"$group": {"_id": "1", "chats": {"$push": {"chat_id": "$chat_id", "name": "$name"}}}}, {"$sort": {"chat_id": 1}}]))
    if chats_user:
        keyboard = VkKeyboard(one_time=True)
        for chat in chats_user[0]["chats"]:
            payload["chat_id"] = chat["chat_id"]
            if "name" not in chat:
                chat.update({"name" : chat["chat_id"]})
            if "name" in chat and chat["name"] == "":
                chat["name"] = chat["chat_id"]
            keyboard.add_button(chat["name"], color=VkKeyboardColor.SECONDARY, payload=payload)
            if (list(chats_user[0]["chats"]).index(chat) + 1) % 3 == 0 and list(chats_user[0]["chats"]).index(chat) != 0:
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
                attachmentslist.append(attachment["type"]+str(attachment[attachment["type"]]["from_id"])+'_'+str(attachment[attachment["type"]]["id"]))
            except:
                traceback.print_exc()
                print(1)
        else:
            try:
                print(attachment)
                attachmentslist.append(attachment["type"]+str(attachment[attachment["type"]]["owner_id"])+'_'+str(attachment[attachment["type"]]["id"]))
            except:
                traceback.print_exc()
                print(1)
    print(attachmentslist)
    for user_id in user_ids:
        try:
            vk.messages.send(user_id=user_id, message=message, attachment=','.join(attachmentslist), random_id=int(vk_api.utils.get_random_id()))
        except:
            traceback.print_exc()
            print("не получилось")
def log_txt(ex_cls, ex, tb):
    with open('error.txt', 'w', encoding='utf-8') as f:
        text = '{}: {}:\n'.format(ex_cls.__name__, ex)
        text += ''.join(traceback.format_tb(tb))
        f.write(text)
    quit()
sys.excepthook = log_txt

downloads()

client = pymongo.MongoClient(host, port)
db = client.kristybot
chats = db.chats
statuschats = chats.find()

vk_session = vk_api.VkApi(token=tokentext)
vk = vk_session.get_api()
vklong = VkBotLongPoll(vk_session, group_id)
upload = VkUpload(vk_session)

serverporok = threading.Thread(target=server)
serverporok.start()

for event in vklong.listen():
    if event.type == VkBotEventType.MESSAGE_NEW and event.from_chat and 'action' in event.object.message and event.object.message['action']['type'] == 'chat_invite_user' and int(abs(event.object.message['action']['member_id'])) == int(group_id):
        vk.messages.send(chat_id=1, message="Бот добавлен в группу: " + str(event.chat_id), random_id=int(vk_api.utils.get_random_id()))
        if not chats.find_one({"chat_id": event.chat_id}):
            chats.insert_one({"chat_id": event.chat_id, "name": "", "members": [{"user_id": event.object.message["from_id"], "rank": 2, "all": 0}], "groups": []})
            vk.messages.send(chat_id=event.chat_id, message="Приветик, рада всех видеть! в беседе №{}\n".format(str(event.chat_id)) +
                                                            "Для того, чтобы мы смогли общаться -> предоставьте мне доступ ко всей переписке \n"
                                                            "Я здесь новенькая, поэтому моя база данных о каждом из вас пуста((( \n"
                                                            "Чтобы познакомиться со мной и я смогла узнать о вас лучше -> напишите любое сообщение в чат \n"
                                                            "Или вы можете дать мне права администратора, после чего прописать команду !download, тем самым загрузив всех пользователей одновременно! \n"
                                                            "Также попрошу короля назначить имя этой беседы, через !name <имя>, которое будет использоваться в рассылках.", random_id=int(vk_api.utils.get_random_id()))
    elif event.type == VkBotEventType.MESSAGE_NEW and event.from_chat and 'action' in event.object.message and (event.object.message['action']['type'] == 'chat_invite_user' or event.object.message['action']['type'] == 'chat_invite_user_by_link') and event.object.message['action']['member_id'] > 0:
        try:
            checkUser(event.chat_id, event.object.message['action']['member_id'])
            vk.messages.send(chat_id=event.chat_id, message="Добро пожаловать в нашу беседу)))", random_id=int(vk_api.utils.get_random_id()))
        except:
            vk.messages.send(chat_id=event.chat_id, message="Новый пользователь не добавлен(((", random_id=int(vk_api.utils.get_random_id()))
    elif event.type == VkBotEventType.MESSAGE_NEW and event.from_chat:
        checkUser(event.chat_id, event.object.message["from_id"])
        if re.findall(r'^!(\w+)', event.object.message["text"]) and not re.findall(r"\[club+(\d+)\|\W*\w+\]", event.object.message["text"]):
            event.object.message["text"] = event.object.message["text"].lower()  # тестируем
            command = re.findall(r'^!(\w+)', event.object.message["text"])[0]
            # Команды, которые только с админкой
            if command == "создать":
                try:
                    groups_off = []
                    groups_on = []
                    if not re.findall(r"(?<=\s)[a-zA-Zа-яА-ЯёЁ\d]+(?=\s|$)", event.object.message["text"]):
                        vk.messages.send(chat_id=event.chat_id, message="Вы не ввели группы, либо использовали запрешённые символы в названиях", random_id=int(vk_api.utils.get_random_id()))
                        continue
                    groups_find = list(set(re.findall(r"(?<=\s)[a-zA-Zа-яА-ЯёЁ\d]+(?=\s|$)", event.object.message["text"])) - set(["all", "все", "online", "онлайн"]))
                    groups_off = list(set(groups_find) - set(chats.distinct("groups.name", {"chat_id": event.chat_id})))
                    groups_on = list(set(groups_find) - set(groups_off))
                    groups_off.sort()
                    groups_on.sort()

                    name_vk = vk.users.get(user_id=event.object.message["from_id"])
                    name = name_vk[0]["first_name"] + " " + name_vk[0]["last_name"]
                    for group in groups_off:
                        chats.update_one({"chat_id": event.chat_id}, {"$push": {"groups": {"name": group, "creator": event.object.message["from_id"], "members": [], "kicked": [], "info": ""}}})
                    if not groups_on and groups_off:
                        test = vk.messages.send(chat_id=event.chat_id, message=name + "\nЯ добавила все ниже перечисленные группы:\n➕ " + '\n➕ '.join(groups_off), random_id=int(vk_api.utils.get_random_id()))
                    else:
                        if not groups_off:
                            vk.messages.send(chat_id=event.chat_id, message=name + "\nВсе группы и так уже добавлены:\n✔ " + '\n✔ '.join(groups_on), random_id=int(vk_api.utils.get_random_id()))
                        else:
                            vk.messages.send(chat_id=event.chat_id, message=name + "\nЯ добавила все нижеперечисленные группы:\n➕ " + '\n➕ '.join(groups_off)
                                                                            + "\nНо также некоторые группы уже были добавлены ранее:\n✔ " + '\n✔ '.join(groups_on), random_id=int(vk_api.utils.get_random_id()))
                except Exception as ex:
                    traceback.print_exc()
                    vk.messages.send(chat_id=event.chat_id, message="Что-то пошло не так(((", random_id=int(vk_api.utils.get_random_id()))
            elif command == "удалить":
                try:
                    groups_on = []
                    groups_off = []
                    groups_error = []
                    if not re.findall(r"(?<=\s)[a-zA-Zа-яА-ЯёЁ\d]+(?=\s|$)", event.object.message["text"]):
                        vk.messages.send(chat_id=event.chat_id, message="Вы не ввели группы, либо использовали запрешённые символы в названиях", random_id=int(vk_api.utils.get_random_id()))
                        continue
                    groups_find = list(set(re.findall(r"(?<=\s)[a-zA-Zа-яА-ЯёЁ\d]+(?=\s|$)", event.object.message["text"])) - set(["all", "все", "online", "онлайн"]))
                    groups_off = list(set(groups_find) - set(chats.distinct("groups.name", {"chat_id": event.chat_id})))
                    groups_on = list(set(groups_find) - set(groups_off))

                    if not chats.find_one({"chat_id": event.chat_id, "members": {"$elemMatch": {"user_id": {"$eq": event.object.message["from_id"]}, "rank": {"$gt": 0}}}}, {"_id": 0, "members.user_id.$": 1}):
                        groups_user = list(chats.aggregate([{"$unwind": "$groups"}, {"$match": {"$and": [{"chat_id": event.chat_id}, {"groups.creator": {"$eq": event.object.message["from_id"]}}]}}, {"$group": {"_id": "$chat_id", "groups": {"$push": "$groups.name"}}}]))
                        if groups_user:
                            groups_error = list(set(groups_on) - set(groups_user[0]["groups"]))
                            groups_on = list(set(groups_on) - set(groups_error))
                    for group in groups_on:
                        chats.update_one({"chat_id": event.chat_id}, {'$pull': {"groups": {"name": group}}})

                    groups_off.sort()
                    groups_on.sort()
                    groups_error.sort()

                    name_vk = vk.users.get(user_id=event.object.message["from_id"])
                    name = name_vk[0]["first_name"] + " " + name_vk[0]["last_name"]
                    if not groups_off and not groups_error:
                        vk.messages.send(chat_id=event.chat_id, message=name + "\nЯ удалила эти группы:\n✖ " + '\n✖ '.join(groups_on), random_id=int(vk_api.utils.get_random_id()))
                    elif not groups_on and not groups_error:
                        vk.messages.send(chat_id=event.chat_id, message=name + "\nЭтих групп и так нет в беседе:\n⛔ " + '\n⛔ '.join(groups_off), random_id=int(vk_api.utils.get_random_id()))
                    elif not groups_on and not groups_off:
                        vk.messages.send(chat_id=event.chat_id, message=name + "\nК сожалению, вы не создавали эти группы:\n🚫 " + '\n🚫 '.join(groups_error), random_id=int(vk_api.utils.get_random_id()))
                    elif groups_on and groups_off and not groups_error:
                        vk.messages.send(chat_id=event.chat_id, message=name + "\nЯ удалила эти группы:\n✖ " + '\n✖ '.join(groups_on)
                                                                        + "\nНо эти группы я не нашла в беседе:\n⛔ " + '\n⛔ '.join(groups_off), random_id=int(vk_api.utils.get_random_id()))
                    elif groups_on and not groups_off and groups_error:
                        vk.messages.send(chat_id=event.chat_id, message=name + "\nЯ удалила эти группы:\n✖ " + '\n✖ '.join(groups_on)
                                                                        + "\nНо есть группы, которые вы не создавали и не сможете удалить:\n🚫" + '\n🚫 '.join(groups_error), random_id=int(vk_api.utils.get_random_id()))
                    elif not groups_on and groups_off and groups_error:
                        vk.messages.send(chat_id=event.chat_id, message=name + "\nЭтих групп нет в беседе:\n⛔ " + '\n⛔ '.join(groups_off)
                                                                        + "\nА также есть группы, которые вы не создавали и не сможете удалить:\n🚫" + '\n🚫 '.join(groups_error), random_id=int(vk_api.utils.get_random_id()))
                    elif  groups_on and groups_off and groups_error:
                        vk.messages.send(chat_id=event.chat_id, message=name + "\nЯ успешно удалили эти группы:\n✖ " + '\n✖ '.join(groups_on)
                                                                        + "\nНо вот этих этой беседе нет:\n⛔ " + '\n⛔ '.join(groups_off)
                                                                        + "\nА ещё есть группы, которые вы не создавали и не сможете удалить:\n🚫" + '\n🚫 '.join(groups_error), random_id=int(vk_api.utils.get_random_id()))
                except Exception as ex:
                    traceback.print_exc()
                    vk.messages.send(chat_id=event.chat_id, message="Что-то пошло не так(((", random_id=int(vk_api.utils.get_random_id()))
            elif command == "подключиться":
                try:
                    groups_on = []#есть
                    groups_off = []#нету, добавили
                    groups_error = []#нету таких групп
                    if not re.findall(r"(?<=\s)[a-zA-Zа-яА-ЯёЁ\d]+(?=\s|$)", event.object.message["text"]):
                        vk.messages.send(chat_id=event.chat_id, message="Вы не ввели группы, либо использовали запрешённые символы в названиях", random_id=int(vk_api.utils.get_random_id()))
                        continue
                    groups_find = list(set(re.findall(r"(?<=\s)[a-zA-Zа-яА-ЯёЁ\d]+(?=\s|$)", event.object.message["text"])) - set(["all", "все", "online", "онлайн"]))
                    groups_error = list(set(groups_find) - set(chats.distinct("groups.name", {"chat_id": event.chat_id})))
                    groups_on = list(set(groups_find) - set(groups_error))
                    groups_user = list(chats.aggregate([{"$unwind": "$groups"}, {"$match": {"$and": [{"chat_id": event.chat_id}, {"groups.members": {"$eq": event.object.message["from_id"]}}]}}, {"$group": {"_id": "$chat_id", "groups": {"$push": "$groups.name"}}}]))
                    if groups_user:
                        groups_off = list(set(groups_on) - set(groups_user[0]["groups"]))
                    else:
                        groups_off = groups_on
                    groups_on = list(set(groups_on) - set(groups_off))
                    for group in groups_off:
                        chats.update_one({"chat_id": event.chat_id, "groups.name": group}, {"$push": {"groups.$.members": event.object.message["from_id"]}})

                    groups_off.sort()
                    groups_on.sort()
                    groups_error.sort()
                    name_vk = vk.users.get(user_id=event.object.message["from_id"])
                    name = name_vk[0]["first_name"] + " " + name_vk[0]["last_name"]
                    if not groups_off and not groups_error:
                        vk.messages.send(chat_id=event.chat_id, message=name + "\nВы уже состоите в этих группах:\n✔ " + '\n✔ '.join(groups_on), random_id=int(vk_api.utils.get_random_id()))
                    elif not groups_on and not groups_error:
                        vk.messages.send(chat_id=event.chat_id, message=name + "\nДобавила вас в эти группы:\n➕ " + '\n➕ '.join(groups_off), random_id=int(vk_api.utils.get_random_id()))
                    elif not groups_on and not groups_off:
                        vk.messages.send(chat_id=event.chat_id, message=name + "\nК сожалению, вы не создавали эти группы:\n🚫 " + '\n🚫 '.join(groups_error), random_id=int(vk_api.utils.get_random_id()))
                    elif groups_on and groups_off and not groups_error:
                        vk.messages.send(chat_id=event.chat_id, message=name + "\nДобавила вас в эти группы:\n➕ " + '\n➕ '.join(groups_off)
                                                                        + "\nНо вот в этих группа вы уже состоите:\n✔ " + '\n✔ '.join(groups_on), random_id=int(vk_api.utils.get_random_id()))
                    elif groups_on and not groups_off and groups_error:
                        vk.messages.send(chat_id=event.chat_id, message=name + "\nВы состоите в этих группах:\n✖ " + '\n✖ '.join(groups_on)
                                                                        + "\nНо ещё есть несуществующие группы:\n🚫" + '\n🚫 '.join(groups_error), random_id=int(vk_api.utils.get_random_id()))
                    elif not groups_on and groups_off and groups_error:
                        vk.messages.send(chat_id=event.chat_id, message=name + "\nДобавила вас в эти группы:\n➕ " + '\n➕ '.join(groups_off)
                                                                        + "\nНо есть группы, которых нет в беседе:\n🚫" + '\n🚫 '.join(groups_error), random_id=int(vk_api.utils.get_random_id()))
                    elif groups_on and groups_off and groups_error:
                        vk.messages.send(chat_id=event.chat_id, message=name + "\nДобавила вас в эти группы:\n➕ " + '\n➕ '.join(groups_on)
                                                                        + "\nНо вот в этих группах вы уже состоите:\n✔ " + '\n✔ '.join(groups_off)
                                                                        + "\nА ещё вот этих групп нет:\n🚫" + '\n🚫 '.join(groups_error), random_id=int(vk_api.utils.get_random_id()))
                except Exception as ex:
                    traceback.print_exc()
                    vk.messages.send(chat_id=event.chat_id, message="Что-то пошло не так(((", random_id=int(vk_api.utils.get_random_id()))
            elif command == "отключиться":
                try:
                    groups_on = []# успешно отключила
                    groups_off = []# вас не было в группе
                    groups_error = []# группы тупа нет

                    if not re.findall(r"(?<=\s)[a-zA-Zа-яА-ЯёЁ\d]+(?=\s|$)", event.object.message["text"]):
                        vk.messages.send(chat_id=event.chat_id, message="Вы не ввели группы, либо использовали запрешённые символы в названиях", random_id=int(vk_api.utils.get_random_id()))
                        continue
                    groups_find = list(set(re.findall(r"(?<=\s)[a-zA-Zа-яА-ЯёЁ\d]+(?=\s|$)", event.object.message["text"])) - set(["all", "все", "online", "онлайн"]))
                    groups_error = list(set(groups_find) - set(chats.distinct("groups.name", {"chat_id": event.chat_id})))
                    groups_on = list(set(groups_find) - set(groups_error))
                    groups_user = list(chats.aggregate([{"$unwind": "$groups"}, {"$match": {"$and": [{"chat_id": event.chat_id}, {"groups.members": {"$eq": event.object.message["from_id"]}}]}}, {"$group": {"_id": "$chat_id", "groups": {"$push": "$groups.name"}}}]))
                    if groups_user:
                        groups_off = list(set(groups_on) - set(groups_user[0]["groups"]))
                        groups_on = list(set(groups_on) - set(groups_off))
                    for group in groups_on:
                        chats.update_one({"chat_id": event.chat_id, "groups.name": group}, {"$pull": {"groups.$.members": event.object.message["from_id"]}})

                    groups_off.sort()
                    groups_on.sort()
                    groups_error.sort()
                    name_vk = vk.users.get(user_id=event.object.message["from_id"])
                    name = name_vk[0]["first_name"] + " " + name_vk[0]["last_name"]
                    if not groups_off and not groups_error:
                        vk.messages.send(chat_id=event.chat_id, message=name + "\nУспешно отключила вас от групп: \n✖ " + '\n✖ '.join(groups_on), random_id=int(vk_api.utils.get_random_id()))
                    elif not groups_on and not groups_error:
                        vk.messages.send(chat_id=event.chat_id, message=name + "\nВас и не было в этих группах: \n⛔ " + '\n⛔ '.join(groups_off), random_id=int(vk_api.utils.get_random_id()))
                    elif not groups_on and not groups_off:
                        vk.messages.send(chat_id=event.chat_id, message=name + "\nК сожалению, но данных групп нет: \n🚫 " + '\n🚫 '.join(groups_error), random_id=int(vk_api.utils.get_random_id()))
                    elif groups_on and groups_off and not groups_error:
                        vk.messages.send(chat_id=event.chat_id, message=name + "\nУспешно отключила вас от групп: \n✖ " + '\n✖ '.join(groups_off)
                                                                        + "\nНо вот в этих группах вас и так не было: \n⛔ " + '\n⛔ '.join(groups_on), random_id=int(vk_api.utils.get_random_id()))
                    elif groups_on and not groups_off and groups_error:
                        vk.messages.send(chat_id=event.chat_id, message=name + "\nУспешно отключила вас от групп: \n✖ " + '\n✖ '.join(groups_on)
                                                                        + "\nНо этих групп ещё нет в беседе: \n🚫" + '\n🚫 '.join(groups_error), random_id=int(vk_api.utils.get_random_id()))
                    elif not groups_on and groups_off and groups_error:
                        vk.messages.send(chat_id=event.chat_id, message=name + "\nВас и не было в этих группах: \n⛔ " + '\n⛔ '.join(groups_off)
                                                                        + "\nДа ещё вы указали несуществующие группы: \n🚫" + '\n🚫 '.join(groups_error), random_id=int(vk_api.utils.get_random_id()))
                    elif groups_on and groups_off and groups_error:
                        vk.messages.send(chat_id=event.chat_id, message=name + "\nУспешно отключила вас от групп: \n✖ " + '\n✖ '.join(groups_on)
                                                                        + "\nНо вот в этих группах вас и так не было: \n⛔ " + '\n⛔ '.join(groups_off)
                                                                        + "\nА ещё вот этих групп в беседе нет: \n🚫" + '\n🚫 '.join(groups_error), random_id=int(vk_api.utils.get_random_id()))
                except Exception as ex:
                    traceback.print_exc()
                    vk.messages.send(chat_id=event.chat_id, message="Что-то пошло не так(((", random_id=int(vk_api.utils.get_random_id()))
            elif command == "подключить":
                try:
                    if chats.find_one({"chat_id": event.chat_id}, {"_id": 0, "members": {"$elemMatch": {"user_id": {"$eq": event.object.message["from_id"]}, "rank": {"$gt": 0}}}}):
                        if '>' not in event.object.message["text"]:
                            vk.messages.send(chat_id=event.chat_id, message="Не найден символ '>'", random_id=int(vk_api.utils.get_random_id()))
                            continue
                        users_find = re.findall(r"\[id+(\d+)\|\W*\w+\]", event.object.message["text"].split('>')[0])
                        users_id_int = [int(user) for user in users_find]
                        if not users_find:
                            vk.messages.send(chat_id=event.chat_id, message="Пользователи не найдены", random_id=int(vk_api.utils.get_random_id()))
                            continue
                        groups_find = list(set(re.findall(r"(?<=\s)[a-zA-Zа-яА-ЯёЁ\d]+(?=\s|$)", event.object.message["text"].split('>')[1])) - set(["all", "все", "online", "онлайн"]))
                        if not groups_find:
                            vk.messages.send(chat_id=event.chat_id, message="Вы не ввели группы, либо использовали запрешённые символы в названиях", random_id=int(vk_api.utils.get_random_id()))
                            continue
                        groups_all = list(chats.aggregate([{"$unwind": "$groups"}, {"$match": {"$and": [{"chat_id": event.chat_id}, {"groups.name": {"$in": groups_find}}]}}, {"$group": {"_id": "$chat_id", "groups": {"$push": "$groups.name"}}}]))[0]["groups"]
                        if not groups_all:
                            vk.messages.send(chat_id=event.chat_id, message="Вы данный момент в группе нет групп", random_id=int(vk_api.utils.get_random_id()))
                            continue

                        users_id_int = [int(user) for user in users_find]

                        members = list(chats.aggregate([{"$unwind": "$members"}, {"$match": {"$and": [{"chat_id": event.chat_id}, {"members.user_id": {"$in": users_id_int}}]}}, {"$group": {"_id": "$chat_id", "members": {"$push": "$members.user_id"}}}]))

                        users_error = list(set(users_id_int) - set(members[0]["members"]))
                        users_ok = list(set(users_id_int) - set(users_error))
                        user_groups = {}
                        for user in users_ok:
                            user_groups.update({user: []})
                            groups_all_user = list(chats.aggregate([{"$unwind": "$groups"}, {"$match": {"$and": [{"chat_id": event.chat_id}, {"groups.members": {"$eq": user}}, {"groups.name": {"$in": groups_all}}]}}, {"$group": {"_id": "$chat_id", "groups": {"$push": "$groups.name"}}}]))
                            if groups_all_user:
                                groups_off = list(set(groups_all) - set(groups_all_user[0]["groups"]))
                            else:
                                groups_off = groups_all
                            for group in groups_off:
                                chats.update_one({"chat_id": event.chat_id, "groups.name": group}, {"$push": {"groups.$.members": user}})
                                user_groups[user].append(group)
                            if not user_groups[user]:
                                del user_groups[user]
                        message = ""
                        first_names_list = vk.users.get(user_ids=list(user_groups.keys()))
                        first_names_dict = {}
                        for first_name in first_names_list:
                            first_names_dict.update({first_name["id"]: first_name["first_name"]})
                        for user in first_names_dict.items():
                            message += "[id{0}|{1}]".format(str(user[0]), user[1]) + ' > ' + ', '.join(user_groups[user[0]]) + "\n"

                        if users_error:
                            try:
                                first_names_dict = {}
                                message += "Данных пользователей нет в базе данных! Если они есть в беседе, то попросите их написать что-то в чат, либо загрузите всех участнков через !download(нужны права администратора) \n"
                                first_names_list = vk.users.get(user_ids=list(users_error))
                                for first_name in first_names_list:
                                    first_names_dict.update({str(first_name["id"]): first_name["first_name"]})
                                for user in users_error:
                                    message += "[id{0}|{1}]".format(str(user), first_names_dict[str(user)]) + " "
                            except:
                                print("error")
                        if message:
                            if user_groups:
                                message = "Добавила \n" + message
                            vk.messages.send(chat_id=event.chat_id, message=message, random_id=int(vk_api.utils.get_random_id()))
                        else:
                            vk.messages.send(chat_id=event.chat_id, message="Данные пользователи уже состоят в этих группах", random_id=int(vk_api.utils.get_random_id()))
                    else:
                        vk.messages.send(chat_id=event.chat_id, message="У вас нет прав админа или короля", random_id=int(vk_api.utils.get_random_id()))
                except Exception as ex:
                    traceback.print_exc()
                    vk.messages.send(chat_id=event.chat_id, message="Что-то пошло не так(((", random_id=int(vk_api.utils.get_random_id()))
            elif command == "отключить":
                try:
                    if chats.find_one({"chat_id": event.chat_id}, {"_id": 0, "members": {"$elemMatch": {"user_id": {"$eq": event.object.message["from_id"]}, "rank": {"$gt": 0}}}}):
                        usersall = chats.distinct("members.user_id", {"chat_id": event.chat_id})
                        groupsall = chats.distinct("groups.name", {"chat_id": event.chat_id})
                        user_groups = {}
                        for user in re.findall(r"\[id+(\d+)\|\W*\w+\]", event.object.message["text"].split('>')[0]):
                            user_groups.update({user: []})
                            for group in re.findall(r"(?<=\s)[a-zA-Zа-яА-ЯёЁ\d]+(?=\s|$)", event.object.message["text"].split('>')[1]):
                                if int(user) in usersall and group in groupsall and chats.find_one({"chat_id": event.chat_id, "groups": {"$elemMatch": {"name": {"$eq": group}, "members": {"$eq": int(user)}}}}, {"_id": 0, "groups.name.$": 1}):
                                    chats.update_one({"chat_id": event.chat_id, "groups.name": group}, {'$pull': {"groups.$.members": int(user)}})
                                    user_groups[user].append(group)
                            if not user_groups[user]:
                                del user_groups[user]
                        message = "Отключила:\n"
                        first_names_list = vk.users.get(user_ids=list(user_groups.keys()))
                        first_names_dict = {}
                        for first_name in first_names_list:
                            first_names_dict.update({str(first_name["id"]): first_name["first_name"]})
                        for user in user_groups:
                            message += "[id{0}|{1}]".format(str(user), first_names_dict[str(user)]) + ' > ' + ', '.join(user_groups[user]) + "\n"
                        if message != "Отключила:\n":
                            vk.messages.send(chat_id=event.chat_id, message=message, random_id=int(vk_api.utils.get_random_id()))
                        else:
                            vk.messages.send(chat_id=event.chat_id, message="Данные пользователи не состоят в этих группах", random_id=int(vk_api.utils.get_random_id()))
                    else:
                        vk.messages.send(chat_id=event.chat_id, message="У вас нет прав админа или короля", random_id=int(vk_api.utils.get_random_id()))
                except Exception as ex:
                    traceback.print_exc()
                    vk.messages.send(chat_id=event.chat_id, message="Что-то пошло не так(((", random_id=int(vk_api.utils.get_random_id()))
            elif command == "переименовать":
                try:
                    groups_find = re.findall(r"(?<=\s)[a-zA-Zа-яА-ЯёЁ\d]+(?=\s|$)", event.object.message["text"])
                    if len(groups_find) < 2:
                        vk.messages.send(chat_id=event.chat_id, message="Неправильный формат", random_id=int(vk_api.utils.get_random_id()))
                        continue
                    elif groups_find[1] in ["all", "все", "online", "онлайн"]:
                        vk.messages.send(chat_id=event.chat_id, message="Новое название является запрещённым", random_id=int(vk_api.utils.get_random_id()))
                        continue
                    name_old = groups_find[0]
                    name_new = groups_find[1]
                    groups_all = chats.distinct("groups.name", {"chat_id": event.chat_id})
                    if name_old not in groups_all:
                        vk.messages.send(chat_id=event.chat_id, message="Не найдена группа с именем: " + name_old, random_id=int(vk_api.utils.get_random_id()))
                        continue
                    elif name_new in groups_all:
                        vk.messages.send(chat_id=event.chat_id, message="Новое имя уже есть в базе данных: " + name_new, random_id=int(vk_api.utils.get_random_id()))
                        continue
                    chats.update_one({"chat_id": event.chat_id, "groups.name": name_old}, {"$set": {"groups.$.name": name_new}})
                    vk.messages.send(chat_id=event.chat_id, message="Успешно установила новое имя: " + name_new, random_id=int(vk_api.utils.get_random_id()))
                except Exception as ex:
                    traceback.print_exc()
                    vk.messages.send(chat_id=event.chat_id, message="Что-то пошло не так(((", random_id=int(vk_api.utils.get_random_id()))

            # Системные команды
            elif command == "admin":
                try:
                    if chats.find_one({"chat_id": event.chat_id, "members": {"$elemMatch": {"user_id": {"$eq": event.object.message["from_id"]}, "rank": {"$gt": 0}}}}, {"_id": 0, "members.user_id.$": 1}):
                        admins = []
                        users_error = []
                        users_find = re.findall(r"\[id+(\d+)\|\W*\w+\]", event.object.message["text"])
                        if not users_find:
                            vk.messages.send(chat_id=event.chat_id, message="Вы не указали пользователей", random_id=int(vk_api.utils.get_random_id()))
                            continue
                        users_id_int = [int(user) for user in users_find]

                        members = list(chats.aggregate([{"$unwind": "$members"}, {"$match": {"$and": [{"chat_id": event.chat_id}, {"members.user_id": {"$in": users_id_int}}, {"members.rank": {"$eq": 0}}]}}, {"$group": {"_id": "$chat_id", "members": {"$push": "$members.user_id"}}}]))

                        if members:
                            users_not = list(set(users_id_int) - set(members[0]["members"]))

                            users = vk.users.get(user_ids=members[0]["members"])
                            for user in users:
                                chats.update_one({"chat_id": event.chat_id, "members.user_id": int(user["id"])}, {"$set": {"members.$.rank": 1}})
                                admins.append("[id{0}|{1}]".format(str(user["id"]), user["first_name"]))
                        else:
                            users_not = users_id_int

                        members_admin = list(chats.aggregate([{"$unwind": "$members"}, {"$match": {"$and": [{"chat_id": event.chat_id}, {"members.user_id": {"$in": users_not}}, {"members.rank": {"$qt": 0}}]}}, {"$group": {"_id": "$chat_id", "members": {"$push": "$members.user_id"}}}]))
                        if members_admin:
                            users_not = list(set(users_not) - set(members_admin[0]["members"]))

                        if users_not:
                            users = vk.users.get(user_ids=users_not)
                            for user in users:
                                users_error.append("[id{0}|{1}]".format(str(user["id"]), user["first_name"]))

                        if admins and users_error:
                            vk.messages.send(chat_id=event.chat_id, message="Поздравляем новых админов!!!: " + ', '.join(admins)
                                                                            + "\nА также некоторых пользователей нет в базе данных. Попросите их написать сообщение в чат, либо используйте !download(с админ правами): \n@id" + " \n@id".join(users_error), random_id=int(vk_api.utils.get_random_id()))
                        elif admins and not users_error:
                            vk.messages.send(chat_id=event.chat_id, message="Поздравляем новых админов!!!: " + ', '.join(admins), random_id=int(vk_api.utils.get_random_id()))
                        elif not admins and users_error:
                            vk.messages.send(chat_id=event.chat_id, message="Пользователей нет в базе данных. Попросите их написать сообщение в чат, либо используйте !download(с админ правами): \n@id" + " \n@id".join(users_error), random_id=int(vk_api.utils.get_random_id()))
                    else:
                        vk.messages.send(chat_id=event.chat_id, message="У вас нет прав админа или короля", random_id=int(vk_api.utils.get_random_id()))
                except Exception as ex:
                    traceback.print_exc()
                    vk.messages.send(chat_id=event.chat_id, message=traceback.print_exc(), random_id=int(vk_api.utils.get_random_id()))
            elif command == "unadmin":
                try:
                    admins = []
                    if chats.find_one({"chat_id": event.chat_id, "members": {"$elemMatch": {"user_id": {"$eq": event.object.message["from_id"]}, "rank": {"$eq": 2}}}}, {"_id": 0, "members.user_id.$": 1}):
                        users_id = re.findall(r"\[id+(\d+)\|\W*\w+\]", event.object.message["text"])
                        for user in users_id:
                            member = chats.find_one({"chat_id": event.chat_id}, {"_id": 0, "members": {"$elemMatch": {"user_id": {"$eq": int(user)}}}})
                            if member and member["members"][0]["rank"] == 1:
                                first_name = vk.users.get(user_id=user)[0]["first_name"] #оптимизировать
                                chats.update_one({"chat_id": event.chat_id, "members.user_id": int(user)}, {"$set": {"members.$.rank": 0}})
                                admins.append("[id{0}|{1}]".format(str(user), first_name))
                        if admins:
                            vk.messages.send(chat_id=event.chat_id, message="Мы прощаемся с этими людьми в рядах админов: " + ', '.join(admins), random_id=int(vk_api.utils.get_random_id()))
                        else:
                            vk.messages.send(chat_id=event.chat_id, message="Похоже, все уже и так не в админах, либо их нет в беседе", random_id=int(vk_api.utils.get_random_id()))
                    else:
                        vk.messages.send(chat_id=event.chat_id, message="Вы не король", random_id=int(vk_api.utils.get_random_id()))
                except Exception as ex:
                    traceback.print_exc()
                    vk.messages.send(chat_id=event.chat_id, message="Что-то пошло не так(((", random_id=int(vk_api.utils.get_random_id()))
            elif command == "king":
                try:
                    if chats.find_one({"chat_id": event.chat_id, "members": {"$elemMatch": {"user_id": {"$eq": event.object.message["from_id"]}, "rank": {"$eq": 2}}}}, {"_id": 0, "members.user_id.$": 1}):
                        user = re.findall(r"\[id+(\d+)\|\W*\w+\]", event.object.message["text"])[0]
                        member = chats.find_one({"chat_id": event.chat_id, "members": {"$elemMatch": {"$and": [{"user_id": {"$eq": int(user)}}, {"user_id": {"$ne": event.object.message["from_id"]}}]}}}, {"_id": 0, "members.user_id.$": 1})
                        if member:
                            first_name = vk.users.get(user_id=user)[0]["first_name"]
                            chats.update_one({"chat_id": event.chat_id, "members.user_id": int(user)}, {"$set": {"members.$.rank": 2}})
                            chats.update_one({"chat_id": event.chat_id, "members.user_id": int(event.object.message["from_id"])}, {"$set": {"members.$.rank": 1}})
                            vk.messages.send(chat_id=event.chat_id, message="ПРИВЕТСТВУЙТЕ НОВОГО КОРОЛЯ: " + "[id{0}|{1}]".format(str(user), first_name), random_id=int(vk_api.utils.get_random_id()))
                        else:
                            vk.messages.send(chat_id=event.chat_id, message="Похоже его нет в беседе, либо вы хотели сделать себя НОВЫМ КОРОЛЁМ", random_id=int(vk_api.utils.get_random_id()))
                    else:
                        vk.messages.send(chat_id=event.chat_id, message="Вы не король", random_id=int(vk_api.utils.get_random_id()))
                except Exception as ex:
                    traceback.print_exc()
                    vk.messages.send(chat_id=event.chat_id, message="Что-то пошло не так(((", random_id=int(vk_api.utils.get_random_id()))
            elif command == "ранги":
                try:
                    king = list(chats.aggregate([{"$unwind": "$members"}, {"$match": {"$and": [{"chat_id": event.chat_id}, {"members.rank": {"$eq": 2}}]}}, {"$group": {"_id": "$chat_id", "king": {"$push": "$members.user_id"}}}]))[0]["king"][0]
                    admins_find = list(chats.aggregate([{"$unwind": "$members"}, {"$match": {"$and": [{"chat_id": event.chat_id}, {"members.rank": {"$eq": 1}}]}}, {"$group": {"_id": "$chat_id", "admins": {"$push": "$members.user_id"}}}]))

                    king = vk.users.get(user_id=king)[0]
                    kingtext = "👑 " + king["first_name"] + " " + king["last_name"] + " \n"
                    admin_text = ""
                    if admins_find:
                        admins_info = vk.users.get(user_ids=admins_find[0]["admins"])
                        for admin in admins_info:
                            admin_text += "😈 " + admin["first_name"] + " " + admin["last_name"] + " \n"
                    vk.messages.send(chat_id=event.chat_id, message=kingtext + admin_text, random_id=int(vk_api.utils.get_random_id()))
                except Exception as ex:
                    traceback.print_exc()
                    vk.messages.send(chat_id=event.chat_id, message="Что-то пошло не так(((", random_id=int(vk_api.utils.get_random_id()))
            elif command == "неделя":
                if int(time.strftime("%W", time.localtime(time.time() + 3600))) % 2 == 0:
                    vk.messages.send(chat_id=event.chat_id, message="НИЖНЯЯ НЕДЕЛЯ", random_id=int(vk_api.utils.get_random_id()))
                else:
                    vk.messages.send(chat_id=event.chat_id, message="ВЕРХНЯЯ НЕДЕЛЯ", random_id=int(vk_api.utils.get_random_id()))
            elif command == "бфу":
                vk.messages.send(chat_id=event.chat_id, attachment="photo-199300529_457239023", random_id=int(vk_api.utils.get_random_id()))
            elif command == "аня":
                vk.messages.send(chat_id=event.chat_id, attachment="photo-199300529_457239031", random_id=int(vk_api.utils.get_random_id()))
            elif command == "пиздец":
                vk.messages.send(chat_id=event.chat_id, attachment="photo-199300529_457239032", random_id=int(vk_api.utils.get_random_id()))
            elif command == "похуй":
                vk.messages.send(chat_id=event.chat_id, attachment="photo-199300529_457239033", random_id=int(vk_api.utils.get_random_id()))
            elif command == "бабенко":
                vk.messages.send(chat_id=event.chat_id, attachment="photo-199300529_457239034", random_id=int(vk_api.utils.get_random_id()))
            elif command == "руслан":
                try:
                    message_text = "Играем в русскую рулетку. И проиграл у нас: "
                    all_ids = chats.distinct("members.user_id", {"chat_id": event.chat_id})
                    random_id = all_ids[vk_api.utils.get_random_id() % len(all_ids)]
                    user_photo = vk.users.get(user_id=random_id, fields=["photo_id"])[0]["photo_id"]
                    vk.messages.send(chat_id=event.chat_id, message=message_text, attachment="photo" + str(user_photo), random_id=int(vk_api.utils.get_random_id()))
                except:
                    vk.messages.send(chat_id=event.chat_id, message="Не повезло", random_id=int(vk_api.utils.get_random_id()))
            elif command == "жопа":
                vk.messages.send(chat_id=event.chat_id, attachment="photo-199300529_457239100", random_id=int(vk_api.utils.get_random_id()))

        #проверка пингов без +
        if re.findall(r"(?:\s|^)\@([a-zA-Zа-яА-ЯёЁ\d]+)(?=\s|$)", event.object.message["text"]):
            pinglist = []
            for ping in re.findall(r"\@(\w+)", event.object.message["text"].lower()):
                user_ids = chats.find_one({"chat_id": event.chat_id, "groups": {"$elemMatch": {"name": {"$eq": ping}}}}, {"_id": 0, "groups.members.$": 1})
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
                vk.messages.send(chat_id=event.chat_id, message=pinger_text + "☝☝☝☝☝☝☝☝☝☝ \n@" + ' @'.join(list(domains_dict.values())) + " \n☝☝☝☝☝☝☝☝☝☝ ", random_id=int(vk_api.utils.get_random_id()))
        #проверка пингов с +
        if re.findall(r"(?:\s|^)\@([a-zA-Zа-яА-ЯёЁ\d]+)\+(?=\s|$)", event.object.message["text"]):
            pinglist = []
            for ping in re.findall(r"\@(\w+)", event.object.message["text"].lower()):
                user_ids = chats.find_one({"chat_id": event.chat_id, "groups": {"$elemMatch": {"name": {"$eq": ping}}}}, {"_id": 0, "groups.members.$": 1})
                if user_ids:
                    for user_id in user_ids["groups"][0]["members"]:
                        if user_id not in pinglist:
                            pinglist.append(user_id)
            if pinglist:
                user =  vk.users.get(user_id=event.object.message["from_id"])
                name_user = user[0]["first_name"] + ' ' + user[0]["last_name"]
                name = chats.find_one({"chat_id": event.chat_id}, {"_id": 0, "name": 1})
                if not name["name"]:
                    name["name"] = str(event.chat_id)
                sendmessages = threading.Thread(target=sendMessageToUsers,
                                                args=(pinglist, "Отправлено из беседы: " + name["name"]
                                                                + " \nКем: " + name_user
                                                                + ' \nСообщение: ' + event.object.message["text"],
                                                event.object.message["attachments"], ))
                sendmessages.start()
        # подсчёт all
        if re.findall(r"\@all(?=\s|$)", event.object.message["text"]):
            try: # на всякий
                imposter = vk.users.get(user_id=event.object.message["from_id"])[0]
                imposter_text = imposter["first_name"] + " " + imposter["last_name"]
                chats.update_one({"chat_id": event.chat_id, "members.user_id": event.object.message["from_id"]}, {"$inc": {"members.$.all": 1}})
                #vk.messages.send(chat_id=event.chat_id, message=imposter_text +", 😡", random_id=int(vk_api.utils.get_random_id()))
            except:
                print(1)
        # Команды, которые нужны для настроки (доступны только королю)
        if re.findall(r'^!(\w+)', event.object.message["text"]) and chats.find_one({"chat_id": event.chat_id, "members": {"$elemMatch": {"user_id": {"$eq": event.object.message["from_id"]}, "rank": {"$eq": 2}}}}, {"_id": 0, "members.user_id.$": 1}):
            event.object.message["text"] = event.object.message["text"].lower()
            command = re.findall(r'^!(\w+)', event.object.message["text"])[0]
            if command == "download":
                try:
                    usersinfo = vk.messages.getConversationMembers(peer_id=(2000000000 + event.chat_id), group_id=group_id)
                    for member in usersinfo["profiles"]:
                        chats.update_one({"chat_id": event.chat_id, "members.user_id": {"$ne": member["id"]}}, {"$push": {"members": {"user_id": member["id"], "rank": 0}}})
                    vk.messages.send(chat_id=event.chat_id, message="Загрузка пользователей прошла успешно", random_id=int(vk_api.utils.get_random_id()))
                except:
                    traceback.print_exc()
                    vk.messages.send(chat_id=event.chat_id, message="Для использования этой команды у меня должна быть админка(((", random_id=int(vk_api.utils.get_random_id()))
            elif command == "name":
                try:
                    chats.update_one({"chat_id": event.chat_id}, {"$set": {"name": event.object.message["text"].split(' ', maxsplit=1)[1]}})
                    vk.messages.send(chat_id=event.chat_id, message="Успешно обновила имя", random_id=int(vk_api.utils.get_random_id()))
                except:
                    vk.messages.send(chat_id=event.chat_id, message="Имя не обновлено", random_id=int(vk_api.utils.get_random_id()))
    elif event.type == VkBotEventType.MESSAGE_NEW and event.from_user:
        try:
            if "payload" in event.object.message:
                event.object.message["payload"] = json.loads(event.object.message["payload"])
                if "chat_id" in event.object.message["payload"] and event.object.message["payload"]["chat_id"] == -1:
                    vk.messages.send(user_id=event.object.message["from_id"], message="Выберите беседу", random_id=int(vk_api.utils.get_random_id()), keyboard=createSelectChatKeyboard(event.object.message["payload"], event.object.message["from_id"]).get_keyboard())
                    continue
                if event.object.message["payload"]["action"] == "groups_all":
                    try:
                        groups_all = chats.distinct("groups.name", {"chat_id": event.object.message["payload"]["chat_id"], "members.user_id": event.object.message["from_id"]})
                        if groups_all:
                            groups_all_text = "Все группы: \n"
                            for number in range(1, len(groups_all) + 1):
                                groups_all_text += str(number) + ". " + groups_all[number - 1] + " \n"
                            vk.messages.send(user_id=event.object.message["from_id"], message=groups_all_text, random_id=int(vk_api.utils.get_random_id()), keyboard=createStartKeyboard().get_keyboard())
                        else:
                            vk.messages.send(user_id=event.object.message["from_id"], message="Не найденно групп в беседе", random_id=int(vk_api.utils.get_random_id()), keyboard=createStartKeyboard().get_keyboard())
                    except Exception as ex:
                        traceback.print_exc()
                        vk.messages.send(user_id=event.object.message["from_id"], message="Что-то пошло не так(((", random_id=int(vk_api.utils.get_random_id()), keyboard=createStartKeyboard().get_keyboard())
                elif event.object.message["payload"]["action"] == "groups_my":
                    groups_my_all = list(chats.aggregate([{"$unwind": "$groups"}, {"$match": {"$and": [{"chat_id": event.object.message["payload"]["chat_id"]}, {"groups.members": {"$eq": event.object.message["from_id"]}}]}}, {"$group": {"_id": "$chat_id", "groups": {"$push": "$groups.name"}}}]))
                    if groups_my_all:
                        groups_my_text = "Группы, в которых вы есть: \n"
                        for number in range(1, len(groups_my_all[0]["groups"]) + 1):
                            groups_my_text += str(number) + ". " + groups_my_all[0]["groups"][number - 1] + " \n"
                        vk.messages.send(user_id=event.object.message["from_id"], message=groups_my_text, random_id=int(vk_api.utils.get_random_id()), keyboard=createStartKeyboard().get_keyboard())
                    else:
                        vk.messages.send(user_id=event.object.message["from_id"], message="Вас нет в группах этой беседы", random_id=int(vk_api.utils.get_random_id()), keyboard=createStartKeyboard().get_keyboard())
                elif event.object.message["payload"]["action"] == "go_to_para":
                    chance = int(vk_api.utils.get_random_id())
                    if chance % 100 == 0 and random.SystemRandom().random.randint(1, 2) == 1:
                        chance = 0
                    elif chance % 100 == 0 and random.SystemRandom().random.randint(1, 2) == 2:
                        chance = 100
                    else:
                        chance %= 100
                    vk.messages.send(user_id=event.object.message["from_id"], message="Рекомендую прогулять пару с вероятностью: " + str(chance) + "%", random_id=int(vk_api.utils.get_random_id()), keyboard=createStartKeyboard().get_keyboard())
                elif event.object.message["payload"]["action"] == "exit_select_chats":
                    vk.messages.send(user_id=event.object.message["from_id"], message="Я вернула вас в меню выбора", random_id=int(vk_api.utils.get_random_id()), keyboard=createStartKeyboard().get_keyboard())

            elif re.findall(r'^!(\w+)', event.object.message["text"]) and not re.findall(r"\[club+(\d+)\|\W*\w+\]", event.object.message["text"]):
                event.object.message["text"] = event.object.message["text"].lower()  # тестируем
                command = re.findall(r'^!(\w+)', event.object.message["text"])[0]
                if command == "помощь":
                    vk.messages.send(user_id=event.object.message["from_id"], message="Команды: \n!моигруппы <номер_чата> - выводит группы, в которых вы состоите в выбраном чате \n"
                                                                                      "!всегруппы <номер_чата> - выводит все группы беседы", keyboard=createStartKeyboard().get_keyboard(), random_id=int(vk_api.utils.get_random_id()))
                if command == "моигруппы":
                    try:
                        groups_my_all = list(chats.aggregate([{"$unwind": "$groups"}, {"$match": {"$and": [{"chat_id": int(event.object.message["text"].split()[1])}, {"groups.members": {"$eq": event.object.message["from_id"]}}]}}, {"$group": {"_id": "$chat_id", "groups": {"$push": "$groups.name"}}}]))
                        if groups_my_all:
                            groups_my_text = "Группы, в которых вы есть: \n"
                            for number in range(1, len(groups_my_all[0]["groups"]) + 1):
                                groups_my_text += str(number) + ". " + groups_my_all[0]["groups"][number - 1] + " \n"
                            vk.messages.send(user_id=event.object.message["from_id"], message=groups_my_text, random_id=int(vk_api.utils.get_random_id()), keyboard=createStartKeyboard().get_keyboard())
                        else:
                            vk.messages.send(user_id=event.object.message["from_id"], message="Вас нет в группах этой беседы", random_id=int(vk_api.utils.get_random_id()), keyboard=createStartKeyboard().get_keyboard())
                    except Exception as ex:
                        traceback.print_exc()
                        vk.messages.send(user_id=event.object.message["from_id"], message="Что-то пошло не так(((", random_id=int(vk_api.utils.get_random_id()))
                elif command == "всегруппы":
                    try:
                        groups_all = chats.distinct("groups.name", {"chat_id": int(event.object.message["text"].split()[1]), "members.user_id": event.object.message["from_id"]})
                        groups_all_text = "Все группы: \n"
                        for number in range(1, len(groups_all) + 1):
                            groups_all_text += str(number) + ". " + groups_all[number - 1] + " \n"
                        vk.messages.send(user_id=event.object.message["from_id"], message=groups_all_text, random_id=int(vk_api.utils.get_random_id()), keyboard=createStartKeyboard().get_keyboard())
                    except Exception as ex:
                        traceback.print_exc()
                        vk.messages.send(user_id=event.object.message["from_id"], message="Что-то пошло не так(((", random_id=int(vk_api.utils.get_random_id()), keyboard=createStartKeyboard().get_keyboard())

            else:
                vk.messages.send(user_id=event.object.message["from_id"], message="Используйте клавиши снизу, либо напишите !помощь", random_id=int(vk_api.utils.get_random_id()), keyboard=createStartKeyboard().get_keyboard())
        except:
            vk.messages.send(user_id=event.object.message["from_id"], message="Что-то пошло не так(((", random_id=int(vk_api.utils.get_random_id()))
