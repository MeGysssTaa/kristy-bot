import os
import re
import time
import traceback
import threading
import requests

import pymongo
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.upload import VkUpload

def downloads():
    global tokentext, group_id, host, port
    pidfile = open(os.path.dirname(__file__) + os.path.sep + 'pid.txt', 'w')
    pidfile.write(str(os.getpid()))
    pidfile.close()

    tokentext = os.environ['VKGROUP_TOKEN']
    group_id = int(os.environ['VKGROUP_ID'])
    host = os.environ['MONGO_HOST']
    port = int(os.environ['MONGO_PORT'])

def sendUpdateMessage():
    global chats, vk
    for chat in chats.find({}, {"_id": 0}):
        try:
            vk.messages.send(chat_id=chat["chat_id"], message="Вышло обновление - теперь я стала лучше!!!", random_id=int(vk_api.utils.get_random_id()))
        except:
            print("я не в беседе " + str(chat["chat_id"]) + "\n")


def checkUser(chat_id, user_id):
    global chats
    try:
        if not chats.find_one({"chat_id": chat_id, "members": {"$eq": user_id}}, {"_id": 0, "members" : 1}) and user_id > 0:
            chats.update_one({"chat_id": chat_id, "members.user_id": {"$ne": user_id}}, {"$push": {"members": {"user_id": user_id, "rank": 0, "all": 0}}})
    except:
        vk.messages.send(chat_id=event.chat_id, message=traceback.print_exc(), random_id=int(vk_api.utils.get_random_id()))


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

downloads()

client = pymongo.MongoClient(host, port)
db = client.kristybot
chats = db.chats
statuschats = chats.find()

vk_session = vk_api.VkApi(token=tokentext)
vk = vk_session.get_api()
vklong = VkBotLongPoll(vk_session, group_id)
upload = VkUpload(vk_session)

sendUpdateMessage()

for event in vklong.listen():
    if event.type == VkBotEventType.MESSAGE_NEW and event.from_chat and 'action' in event.object.message and event.object.message['action']['type'] == 'chat_invite_user' and int(abs(event.object.message['action']['member_id'])) == int(group_id):
        vk.messages.send(chat_id=1, message="Бот добавлен в группу: " + str(event.chat_id), random_id=int(vk_api.utils.get_random_id()))
        print(chats.find_one({"chat_id": event.chat_id}))
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
                    for group in re.findall(r"(?<=\s)[a-zA-Zа-яА-ЯёЁ\d]+(?=\s|$)", event.object.message["text"]):
                        groups = chats.distinct("groups.name", {"chat_id": event.chat_id})
                        stopgroups = ["all", "все", "online", "онлайн"]
                        if group in stopgroups:
                            continue
                        if group in groups:
                            groups_on.append(group)
                        else:
                            chats.update_one({"chat_id": event.chat_id}, {"$push": {"groups": {"name": group, "creator": event.object.message["from_id"], "members": [], "kicked": [], "info": ""}}})
                            groups_off.append(group)

                    if not groups_on and groups_off:
                        test = vk.messages.send(chat_id=event.chat_id, message="Я добавила все ниже перечисленные группы:\n➕ " + '\n➕ '.join(groups_off), random_id=int(vk_api.utils.get_random_id()))
                    else:
                        if not groups_off:
                            vk.messages.send(chat_id=event.chat_id, message="Все группы и так уже добавлены:\n✔ " + '\n✔ '.join(groups_on), random_id=int(vk_api.utils.get_random_id()))
                        else:
                            vk.messages.send(chat_id=event.chat_id, message="Я добавила все нижеперечисленные группы:\n➕ " + '\n➕ '.join(groups_off)
                                                                            + "\nНо также некоторые группы уже были добавлены ранее:\n✔ " + '\n✔ '.join(groups_on), random_id=int(vk_api.utils.get_random_id()))
                except Exception as ex:
                    traceback.print_exc()
                    vk.messages.send(chat_id=event.chat_id, message="Что-то пошло не так(((", random_id=int(vk_api.utils.get_random_id()))
            elif command == "удалить":
                try:
                    groups_on = []
                    groups_off = []
                    groups_error = []
                    for group in event.object.message["text"].split(" ", maxsplit=1)[1].split():
                        groups = chats.distinct("groups.name", {"chat_id": event.chat_id})
                        if group in groups:
                            if chats.distinct("chat_id", {"chat_id": event.chat_id, "$or": [{"members.user_id": event.object.message["from_id"], "$or": [{"members.rank": 2}, {"members.rank": 1}]}, {"groups.name": group, "groups.creator": event.object.message["from_id"]}]}):
                                groups_on.append(group)
                                chats.update_one({"chat_id": event.chat_id}, {'$pull': {"groups": {"name": group}}})
                            else:
                                groups_error.append(group)
                        else:
                            groups_off.append(group)
                    if not groups_off and not groups_error:
                        vk.messages.send(chat_id=event.chat_id, message="Я удалила эти группы:\n✖ " + '\n✖ '.join(groups_on), random_id=int(vk_api.utils.get_random_id()))
                    elif not groups_on and not groups_error:
                        vk.messages.send(chat_id=event.chat_id, message="Этих групп и так нет в беседе:\n⛔ " + '\n⛔ '.join(groups_off), random_id=int(vk_api.utils.get_random_id()))
                    elif not groups_on and not groups_off:
                        vk.messages.send(chat_id=event.chat_id, message="К сожалению, вы не создавали эти группы:\n🚫 " + '\n🚫 '.join(groups_error), random_id=int(vk_api.utils.get_random_id()))
                    elif groups_on and groups_off and not groups_error:
                        vk.messages.send(chat_id=event.chat_id, message="Я удалила эти группы:\n✖ " + '\n✖ '.join(groups_on)
                                                                        + "\nНо эти группы я не нашла в беседе:\n⛔ " + '\n⛔ '.join(groups_off), random_id=int(vk_api.utils.get_random_id()))
                    elif groups_on and not groups_off and groups_error:
                        vk.messages.send(chat_id=event.chat_id, message="Я удалила эти группы:\n✖ " + '\n✖ '.join(groups_on)
                                                                        + "\nНо есть группы, которые вы не создавали и не сможете удалить:\n🚫" + '\n🚫 '.join(groups_error), random_id=int(vk_api.utils.get_random_id()))
                    elif not groups_on and groups_off and groups_error:
                        vk.messages.send(chat_id=event.chat_id, message="Этих групп нет в беседе:\n⛔ " + '\n⛔ '.join(groups_off)
                                                                        + "\nА также есть группы, которые вы не создавали и не сможете удалить:\n🚫" + '\n🚫 '.join(groups_error), random_id=int(vk_api.utils.get_random_id()))
                    elif  groups_on and groups_off and groups_error:
                        vk.messages.send(chat_id=event.chat_id, message="Я успешно удалили эти группы:\n✖ " + '\n✖ '.join(groups_on)
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
                    for group in event.object.message["text"].split(" ", maxsplit=1)[1].split():
                        groups = chats.distinct("groups.name", {"chat_id": event.chat_id})
                        if group in groups:
                            if chats.find_one({"chat_id": event.chat_id, "groups": {"$elemMatch": {"name": {"$eq": group}, "members": {"$eq": event.object.message["from_id"]}}}}, {"_id": 0, "groups.members.$": 1}):
                                groups_on.append(group)
                            else:
                                chats.update_one({"chat_id": event.chat_id, "groups.name": group}, {"$push": {"groups.$.members": event.object.message["from_id"]}})
                                groups_off.append(group)
                        else:
                            groups_error.append(group)
                    if not groups_off and not groups_error:
                        vk.messages.send(chat_id=event.chat_id, message="Вы уже состоите в этих группах:\n✔ " + '\n✔ '.join(groups_on), random_id=int(vk_api.utils.get_random_id()))
                    elif not groups_on and not groups_error:
                        vk.messages.send(chat_id=event.chat_id, message="Добавила вас в эти группы:\n➕ " + '\n➕ '.join(groups_off), random_id=int(vk_api.utils.get_random_id()))
                    elif not groups_on and not groups_off:
                        vk.messages.send(chat_id=event.chat_id, message="К сожалению, вы не создавали эти группы:\n🚫 " + '\n🚫 '.join(groups_error), random_id=int(vk_api.utils.get_random_id()))
                    elif groups_on and groups_off and not groups_error:
                        vk.messages.send(chat_id=event.chat_id, message="Добавила вас в эти группы:\n➕ " + '\n➕ '.join(groups_off)
                                                                        + "\nНо вот в этих группа вы уже состоите:\n✔ " + '\n✔ '.join(groups_on), random_id=int(vk_api.utils.get_random_id()))
                    elif groups_on and not groups_off and groups_error:
                        vk.messages.send(chat_id=event.chat_id, message="Вы состоите в этих группах:\n✖ " + '\n✖ '.join(groups_on)
                                                                        + "\nНо ещё есть несуществующие группы:\n🚫" + '\n🚫 '.join(groups_error), random_id=int(vk_api.utils.get_random_id()))
                    elif not groups_on and groups_off and groups_error:
                        vk.messages.send(chat_id=event.chat_id, message="Добавила вас в эти группы:\n➕ " + '\n➕ '.join(groups_off)
                                                                        + "\nНо есть группы, которых нет в беседе:\n🚫" + '\n🚫 '.join(groups_error), random_id=int(vk_api.utils.get_random_id()))
                    elif groups_on and groups_off and groups_error:
                        vk.messages.send(chat_id=event.chat_id, message="Добавила вас в эти группы:\n➕ " + '\n➕ '.join(groups_on)
                                                                        + "\nНо вот в этих группах вы уже состоите:\n✔ " + '\n✔ '.join(groups_off)
                                                                        + "\nА ещё вот этих групп нет:\n🚫" + '\n🚫 '.join(groups_error), random_id=int(vk_api.utils.get_random_id()))
                except Exception as ex:
                    traceback.print_exc()
                    vk.messages.send(chat_id=event.chat_id, message="Что-то пошло не так(((", random_id=int(vk_api.utils.get_random_id()))
            elif command == "отключиться":
                try:
                    groups_on = []
                    groups_off = []
                    groups_error = []
                    for group in event.object.message["text"].split(" ", maxsplit=1)[1].split():
                        groups = chats.distinct("groups.name", {"chat_id": event.chat_id})
                        if group in groups:
                            if chats.find_one({"chat_id": event.chat_id, "groups": {"$elemMatch": {"name": {"$eq": group}, "members": {"$eq": event.object.message["from_id"]}}}}, {"_id": 0, "groups.members.$": 1}):
                                chats.update_one({"chat_id": event.chat_id, "groups.name": group}, {'$pull': {"groups.$.members": event.object.message["from_id"]}})
                                groups_on.append(group)
                            else:
                                groups_off.append(group)
                        else:
                            groups_error.append(group)

                    if not groups_off and not groups_error:
                        vk.messages.send(chat_id=event.chat_id, message="Успешно отключила вас от групп: \n✖ " + '\n✖ '.join(groups_on), random_id=int(vk_api.utils.get_random_id()))
                    elif not groups_on and not groups_error:
                        vk.messages.send(chat_id=event.chat_id, message="Вас и не было в этих группах: \n⛔ " + '\n⛔ '.join(groups_off), random_id=int(vk_api.utils.get_random_id()))
                    elif not groups_on and not groups_off:
                        vk.messages.send(chat_id=event.chat_id, message="К сожалению, но данных групп нет: \n🚫 " + '\n🚫 '.join(groups_error), random_id=int(vk_api.utils.get_random_id()))
                    elif groups_on and groups_off and not groups_error:
                        vk.messages.send(chat_id=event.chat_id, message="Успешно отключила вас от групп: \n✖ " + '\n✖ '.join(groups_off)
                                                                        + "\nНо вот в этих группах вас и так не было: \n⛔ " + '\n⛔ '.join(groups_on), random_id=int(vk_api.utils.get_random_id()))
                    elif groups_on and not groups_off and groups_error:
                        vk.messages.send(chat_id=event.chat_id, message="Успешно отключила вас от групп: \n✖ " + '\n✖ '.join(groups_on)
                                                                        + "\nНо этих групп ещё нет в беседе: \n🚫" + '\n🚫 '.join(groups_error), random_id=int(vk_api.utils.get_random_id()))
                    elif not groups_on and groups_off and groups_error:
                        vk.messages.send(chat_id=event.chat_id, message="Вас и не было в этих группах: \n⛔ " + '\n⛔ '.join(groups_off)
                                                                        + "\nДа ещё вы указали несуществующие группы: \n🚫" + '\n🚫 '.join(groups_error), random_id=int(vk_api.utils.get_random_id()))
                    elif groups_on and groups_off and groups_error:
                        vk.messages.send(chat_id=event.chat_id, message="Успешно отключила вас от групп: \n✖ " + '\n✖ '.join(groups_on)
                                                                        + "\nНо вот в этих группах вас и так не было: \n⛔ " + '\n⛔ '.join(groups_off)
                                                                        + "\nА ещё вот этих групп в беседе нет: \n🚫" + '\n🚫 '.join(groups_error), random_id=int(vk_api.utils.get_random_id()))
                except Exception as ex:
                    traceback.print_exc()
                    vk.messages.send(chat_id=event.chat_id, message="Что-то пошло не так(((", random_id=int(vk_api.utils.get_random_id()))
            elif command == "подключить":
                try:
                    if chats.find_one({"chat_id": event.chat_id}, {"_id": 0, "members": {"$elemMatch": {"user_id": {"$eq": event.object.message["from_id"]}, "rank": {"$gt": 0}}}}):
                        usersall = chats.distinct("members.user_id", {"chat_id": event.chat_id})
                        groupsall = chats.distinct("groups.name", {"chat_id": event.chat_id})
                        user_groups = {}
                        users_error = []
                        for user in re.findall(r"\[id+(\d+)\|\W*\w+\]", event.object.message["text"].split('>')[0]):
                            user_groups.update({user: []})
                            for group in re.findall(r"(?<=\s)[a-zA-Zа-яА-ЯёЁ\d]+(?=\s|$)", event.object.message["text"].split('>')[1]):
                                if int(user) in usersall:
                                    if group in groupsall and not chats.find_one({"chat_id": event.chat_id, "groups": {"$elemMatch": {"name": {"$eq": group}, "members": {"$eq": int(user)}}}}, {"_id": 0, "groups.name.$": 1}):
                                        chats.update_one({"chat_id": event.chat_id, "groups.name": group}, {"$push": {"groups.$.members": int(user)}})
                                        user_groups[user].append(group)
                                else:
                                    users_error.append(int(user))
                            if not user_groups[user]:
                                del user_groups[user]
                        message = ""
                        first_names_list = vk.users.get(user_ids=list(user_groups.keys()))

                        first_names_dict = {}
                        for first_name in first_names_list:
                            first_names_dict.update({str(first_name["id"]): first_name["first_name"]})
                        for user in user_groups:
                            message += "[id{0}|{1}]".format(str(user), first_names_dict[str(user)]) + ' > ' + ', '.join(user_groups[user]) + "\n"
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
                        if message != "":
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
            # Системные команды
            elif command == "admin":
                try:
                    admins = []
                    users_error = []
                    if chats.find_one({"chat_id": event.chat_id, "members": {"$elemMatch": {"user_id": {"$eq": event.object.message["from_id"]}, "rank": {"$gt": 0}}}}, {"_id": 0, "members.user_id.$": 1}):
                        users_id = re.findall(r"\[id+(\d+)\|\W*\w+\]", event.object.message["text"])

                        for user in users_id:
                            member = chats.find_one({"chat_id": event.chat_id}, {"_id": 0, "members": {"$elemMatch": {"user_id": {"$eq": int(user)}}}})
                            if member:
                                if member["members"][0]["rank"] == 0:
                                    first_name = vk.users.get(user_id=user)[0]["first_name"] #оптимизировать
                                    chats.update_one({"chat_id": event.chat_id, "members.user_id": int(user)}, {"$set": {"members.$.rank": 1}})
                                    admins.append("[id{0}|{1}]".format(str(user), first_name))
                            else:
                                users_error.append(str(user))

                        if admins and users_error:
                            vk.messages.send(chat_id=event.chat_id, message="Поздравляем новых админов!!!: " + ', '.join(admins)
                                                                            + "\nА также некоторых пользователей нет в базе данных. Попросите их написать сообщение в чат, либо используйте !download(с админ правами): \n@id" + " \n@id".join(users_error), random_id=int(vk_api.utils.get_random_id()))
                        elif admins and not users_error:
                            vk.messages.send(chat_id=event.chat_id, message="Поздравляем новых админов!!!: " + ', '.join(admins), random_id=int(vk_api.utils.get_random_id()))
                        elif not admins and users_error:
                            vk.messages.send(chat_id=event.chat_id, message="Пользователей нет в базе данных. Попросите их написать сообщение в чат, либо используйте !download(с админ правами): \n@id" + " \n@id".join(users_error), random_id=int(vk_api.utils.get_random_id()))
                        else:
                            vk.messages.send(chat_id=event.chat_id, message="Все уже в админах", random_id=int(vk_api.utils.get_random_id()))
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
                    members = chats.find_one({"chat_id": event.chat_id}, {"_id": 0, "members.user_id": 1, "members.rank" : 1})
                    admins = []
                    for member in members["members"]:
                        if member["rank"] == 2:
                            king = member["user_id"]
                        elif member["rank"] == 1:
                            admins.append(member["user_id"])
                    king = vk.users.get(user_id=king)
                    kingtext = "👑" + king[0]["first_name"] + " " + king[0]["last_name"]
                    if admins:
                        admins_info = vk.users.get(user_ids=list(admins))
                        adminlist = []
                        for admin in admins_info:
                            adminlist.append(admin["first_name"] + " " + admin["last_name"])
                        vk.messages.send(chat_id=event.chat_id, message=kingtext + ' \n😈' + ' \n😈'.join(adminlist), random_id=int(vk_api.utils.get_random_id()))
                    else:
                        vk.messages.send(chat_id=event.chat_id, message=kingtext, random_id=int(vk_api.utils.get_random_id()))
                except Exception as ex:
                    traceback.print_exc()
                    vk.messages.send(chat_id=event.chat_id, message="Что-то пошло не так(((", random_id=int(vk_api.utils.get_random_id()))
            # Команды, которые доступны без админки
            if command == "неделя":
                if int(time.strftime("%U", time.gmtime())) % 2 == 0:
                    vk.messages.send(chat_id=event.chat_id, message="НИЖНЯЯ НЕДЕЛЯ", random_id=int(vk_api.utils.get_random_id()))
                else:
                    vk.messages.send(chat_id=event.chat_id, message="ВЕРХНЯЯ НЕДЕЛЯ", random_id=int(vk_api.utils.get_random_id()))
            elif command == "бфу":
                vk.messages.send(chat_id=event.chat_id, attachment="photo-199300529_457239023" , random_id=int(vk_api.utils.get_random_id()))

        #проверка пингов без +
        if re.findall(r"(?:\s|^)\@([a-zA-Zа-яА-ЯёЁ\d]+)(?=\s|$)", event.object.message["text"]):
            pinglist = []
            for ping in re.findall(r"\@(\w+)", event.object.message["text"].lower()):
                user_ids = chats.find_one({"chat_id": event.chat_id, "groups": {"$elemMatch": {"name": {"$eq": ping}}}}, {"_id": 0, "groups.members.$": 1})
                if user_ids:
                    for user_id in user_ids["groups"][0]["members"]:
                        if user_id not in pinglist:
                            pinglist.append(user_id)
            domains_list = vk.users.get(user_ids=list(pinglist), fields=["domain"])
            domains_dict = {}
            for domain in domains_list:
                domains_dict.update({str(domain["id"]): domain["domain"]})
            if domains_dict:
                vk.messages.send(chat_id=event.chat_id, message="☝☝☝☝☝☝☝☝☝☝ \n@" + ' @'.join(list(domains_dict.values())) + " \n☝☝☝☝☝☝☝☝☝☝ ", random_id=int(vk_api.utils.get_random_id()))
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
        # Команды, которые нужны для настроки (доступны только королю и админам)
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
                    vk.messages.send(chat_id=event.chat_id, message="Имя не обновленно", random_id=int(vk_api.utils.get_random_id()))
    elif event.type == VkBotEventType.MESSAGE_NEW and event.from_user:
        if re.findall(r'^!(\w+)', event.object.message["text"]) and not re.findall(r"\[club+(\d+)\|\W*\w+\]", event.object.message["text"]):
            event.object.message["text"] = event.object.message["text"].lower()  # тестируем
            command = re.findall(r'^!(\w+)', event.object.message["text"])[0]
            if command == "помощь":
                vk.messages.send(user_id=event.object.message["from_id"], message="Команды \n!моигруппы <номер_чата> - выводит группы, в которых вы состоите в выбраном чате \n"
                                                                                  "!составгруппы <номер_чата> <название_группы> - выводит участников группы \n"
                                                                                  "!всегруппы <номер_чата> - выводит все группы беседы", random_id=int(vk_api.utils.get_random_id()))
            if command == "моигруппы":
                try:
                    find = chats.find_one({"chat_id": int(event.object.message["text"].split()[1])}, {"_id": 0, "groups.members": event.object.message["from_id"], "groups.name": 1})
                    names = []
                    if find and "groups" in find:
                        for group in find["groups"]:
                            if group["members"]:
                                names.append(group["name"])
                    if names:
                        vk.messages.send(user_id=event.object.message["from_id"], message="Ваши группы \n👉🏻" + ' \n👉🏻'.join(names), random_id=int(vk_api.utils.get_random_id()))
                    else:
                        vk.messages.send(user_id=event.object.message["from_id"], message="Пока групп нет, либо вы не в беседе", random_id=int(vk_api.utils.get_random_id()))
                except Exception as ex:
                    traceback.print_exc()
                    vk.messages.send(user_id=event.object.message["from_id"], message="Что-то пошло не так(((", random_id=int(vk_api.utils.get_random_id()))
            elif command == "составгруппы":
                try:
                    find = chats.find_one({"chat_id": int(event.object.message["text"].split()[1])}, {"_id": 0, "groups": {"$elemMatch": {"name": {"$eq": str(event.object.message["text"].split()[2])}}}})
                    if find and "groups" in find and find["groups"]:
                        members = vk.users.get(user_ids=list(find["groups"][0]["members"]))
                        message = "Состав группы: " + event.object.message["text"].split()[2] + " \n"
                        for member in members:
                            message += "👉🏻 " + member["first_name"] + " " + member["last_name"] + " \n"
                        vk.messages.send(user_id=event.object.message["from_id"], message=message, random_id=int(vk_api.utils.get_random_id()))
                    else:
                        vk.messages.send(user_id=event.object.message["from_id"], message="Такой группы нет, либо вы не в беседе", random_id=int(vk_api.utils.get_random_id()))
                except Exception as ex:
                    traceback.print_exc()
                    vk.messages.send(user_id=event.object.message["from_id"], message="Что-то пошло не так(((", random_id=int(vk_api.utils.get_random_id()))
            elif command == "всегруппы":
                try:
                    find = chats.find_one({"chat_id": int(event.object.message["text"].split()[1])}, {"_id": 0, "members": event.object.message["from_id"], "groups.name": 1})
                    names = []
                    if find and "groups" in find:
                        for group in find["groups"]:
                            names.append(group["name"])
                    if names:
                        vk.messages.send(user_id=event.object.message["from_id"], message="Все группы \n👉🏻" + ' \n👉🏻'.join(names), random_id=int(vk_api.utils.get_random_id()))
                    else:
                        vk.messages.send(user_id=event.object.message["from_id"], message="Вас нет в беседе, либо в беседе нет групп", random_id=int(vk_api.utils.get_random_id()))
                except Exception as ex:
                    traceback.print_exc()
                    vk.messages.send(user_id=event.object.message["from_id"], message="Что-то пошло не так(((", random_id=int(vk_api.utils.get_random_id()))