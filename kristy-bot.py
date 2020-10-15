import os
import re
import time
import traceback

import pymongo
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType


def downloads():
    global tokentext, group_id, host, port
    pidfile = open(os.path.dirname(__file__) + os.path.sep + 'pid.txt', 'w')
    pidfile.write(str(os.getpid()))
    pidfile.close()

    tokentext = os.environ['VKGROUP_TOKEN']
    group_id = int(os.environ['VKGROUP_ID'])
    host = os.environ['MONGO_HOST']
    port = int(os.environ['MONGO_PORT'])


downloads()

client = pymongo.MongoClient(host, port)
db = client.kristybot
chats = db.chats
statuschats = chats.find()

vk_session = vk_api.VkApi(token=tokentext)
vk = vk_session.get_api()
vklong = VkBotLongPoll(vk_session, group_id)

for chat in chats.find({}, {"_id": 0, "chat_id": 1}):
    vk.messages.send(chat_id=chat["chat_id"], message="Меня типо обновили ухууу", random_id=int(vk_api.utils.get_random_id()))
for event in vklong.listen():
    if event.type == VkBotEventType.MESSAGE_NEW and event.from_chat and 'action' in event.object.message and event.object.message['action']['type'] == 'chat_invite_user' and abs(event.object.message['action']['member_id']) == group_id:

        if not chats.find_one({"chat_id": event.chat_id}):
            chats.insert_one({"chat_id": event.chat_id, "status": False, "members": [{"user_id": event.object.message["from_id"], "rank": 2}], "groups": []})
        vk.messages.send(chat_id=event.chat_id, message="Для полной работы мне нужна админка(", random_id=int(vk_api.utils.get_random_id()))

    elif event.type == VkBotEventType.MESSAGE_NEW and event.from_chat:
        if re.findall(r'^!(\w+)', event.object.message["text"]):
            event.object.message["text"] = event.object.message["text"].lower()  # тестируем
            command = re.findall(r'^!(\w+)', event.object.message["text"])[0]
            # Команды, которые только с админкой + проверка админки
            if not chats.find_one({"chat_id": event.chat_id})["status"]:
                try:
                    usersinfo = vk.messages.getConversationMembers(peer_id=(2000000000 + event.chat_id), group_id=group_id)
                    for member in usersinfo["profiles"]:
                        chats.update_one({"chat_id": event.chat_id, "members.user_id": {"$ne": member["id"]}}, {"$push": {"members": {"user_id": member["id"], "rank": 0}}})
                    chats.update_one({"chat_id": event.chat_id}, {"$set": {"status": True}})
                    vk.messages.send(chat_id=event.chat_id, message="Я загрузила все данные и готова к бою!", random_id=int(vk_api.utils.get_random_id()))
                except:
                    traceback.print_exc()
                    vk.messages.send(chat_id=event.chat_id, message="Вы пока не дали мне админку(", random_id=int(vk_api.utils.get_random_id()))
                    continue
            elif command == "создать":
                try:
                    groups_off = []
                    groups_on = []
                    for group in re.findall(r"(?<=\s)[a-zA-Zа-яА-ЯёЁ\d]+(?=\s|$)", event.object.message["text"]):
                        groups = chats.distinct("groups.name", {"chat_id": event.chat_id})
                        if group in groups:
                            groups_on.append(group)
                        else:
                            chats.update_one({"chat_id": event.chat_id}, {"$push": {"groups": {"name": group, "creator": event.object.message["from_id"], "members": [], "kicked": [], "info": ""}}})
                            groups_off.append(group)
                    if not groups_on:
                        vk.messages.send(chat_id=event.chat_id, message="Я добавила все ниже перечисленные группы:\n➕ " + '\n➕ '.join(groups_off), random_id=int(vk_api.utils.get_random_id()))
                    else:
                        if not groups_off:
                            vk.messages.send(chat_id=event.chat_id, message="Все группы и так уже добавлены:\n✔ " + '\n✔ '.join(groups_on), random_id=int(vk_api.utils.get_random_id()))
                        else:
                            vk.messages.send(chat_id=event.chat_id, message="Я добавила все нижеперечисленные группы:\n➕ " + '\n➕ '.join(groups_off)
                                                                            + "\nНо также некоторые группы уже были добавлены ранее:\n✔ " + '\n✔ '.join(groups_on), random_id=int(vk_api.utils.get_random_id()))
                except Exception as ex:
                    traceback.print_exc()
                    vk.messages.send(chat_id=event.chat_id, message=traceback.format_exc(), random_id=int(vk_api.utils.get_random_id()))
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

                    vk.messages.send(chat_id=event.chat_id, message="Ниже перечисленны группы, которые вы успешно удалили:\n✖ " + '\n✖ '.join(groups_on)
                                                                    + "\nТакже перечислены группы, которых нет в беседе:\n✖ " + '\n✖ '.join(groups_off)
                                                                    + "\nА также группы, которые вы не создавали и не можете удалить:\n✖ " + '\n✖ '.join(groups_error), random_id=int(vk_api.utils.get_random_id()))
                except Exception as ex:
                    traceback.print_exc()
                    vk.messages.send(chat_id=event.chat_id, message="Что-то пошло не так(((", random_id=int(vk_api.utils.get_random_id()))
            elif command == "подключиться":
                try:
                    groups_off = []
                    groups_on = []
                    groups_error = []
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

                    answer = "Успешно добавила вас в группы: " + ', '.join(groups_off) + "\n"
                    answer += "Вы уже состоите в группах: " + ', '.join(groups_on) + "\n"
                    answer += "Таких групп нет: " + ', '.join(groups_error)

                    vk.messages.send(chat_id=event.chat_id, message=answer, random_id=int(vk_api.utils.get_random_id()))
                except Exception as ex:
                    print(ex)
                    vk.messages.send(chat_id=event.chat_id, message="Что-то пошло не так(((", random_id=int(vk_api.utils.get_random_id()))
            elif command == "отключиться":
                try:
                    groups_on = []
                    groups_off = []
                    groups_error = []
                    for group in event.object.message["text"].split(" ", maxsplit=1)[1].split():
                        groups = chats.distinct("groups.name", {"chat_id": event.chat_id})
                        if group in groups:
                            if chats.distinct("chat_id", {"chat_id": event.chat_id, "groups.name": group, "groups.members": event.object.message["from_id"]}):
                                chats.update_one({"chat_id": event.chat_id, "groups.name": group}, {'$pull': {"groups.$.members": event.object.message["from_id"]}})
                                groups_on.append(group)
                            else:
                                groups_off.append(group)
                        else:
                            groups_error.append(group)

                    answer = "Успешно отключила вас от групп: " + ', '.join(groups_on) + "\n"
                    answer += "Вы не состоите в группах: " + ', '.join(groups_off) + "\n"
                    answer += "Таких групп нет: " + ', '.join(groups_error)

                    vk.messages.send(chat_id=event.chat_id, message=answer, random_id=int(vk_api.utils.get_random_id()))
                except Exception as ex:
                    traceback.print_exc()
                    vk.messages.send(chat_id=event.chat_id, message="Что-то пошло не так(((", random_id=int(vk_api.utils.get_random_id()))
            elif command == "подключить":
                try:
                    if chats.find_one({"chat_id": event.chat_id}, {"_id": 0, "members": {"$elemMatch": {"user_id": {"$eq": event.object.message["from_id"]}, "rank": {"$gt": 0}}}}):
                        usersall = chats.distinct("members.user_id", {"chat_id": event.chat_id})
                        groupsall = chats.distinct("groups.name", {"chat_id": event.chat_id})
                        user_groups = {}
                        for user in re.findall(r"\[id+(\d+)\|\W*\w+\]", event.object.message["text"].split('>')[0]):
                            user_groups.update({user: []})
                            for group in re.findall(r"(?<=\s)[a-zA-Zа-яА-ЯёЁ\d]+(?=\s|$)", event.object.message["text"].split('>')[1]):
                                if int(user) in usersall and group in groupsall and not chats.find_one({"chat_id": event.chat_id, "groups": {"$elemMatch": {"name": {"$eq": group}, "members": {"$eq": int(user)}}}}, {"_id": 0, "groups.name.$": 1}):
                                    chats.update_one({"chat_id": event.chat_id, "groups.name": group}, {"$push": {"groups.$.members": int(user)}})
                                    user_groups[user].append(group)
                            if not user_groups[user]:
                                del user_groups[user]
                        message = "Добавила:\n"
                        first_names_list = vk.users.get(user_ids=list(user_groups.keys()))
                        first_names_dict = {}
                        for first_name in first_names_list:
                            first_names_dict.update({str(first_name["id"]): first_name["first_name"]})
                        for user in user_groups:
                            message += "[id{0}|{1}]".format(str(user), first_names_dict[str(user)]) + ' > ' + ', '.join(user_groups[user]) + "\n"
                        if message != "Добавила:\n":
                            vk.messages.send(chat_id=event.chat_id, message=message, random_id=int(vk_api.utils.get_random_id()))
                        else:
                            vk.messages.send(chat_id=event.chat_id, message="1", random_id=int(vk_api.utils.get_random_id()))
                    else:
                        vk.messages.send(chat_id=event.chat_id, message="У вас нет прав админа или короля", random_id=int(vk_api.utils.get_random_id()))
                except Exception as ex:
                    traceback.print_exc()
                    vk.messages.send(chat_id=event.chat_id, message=traceback.format_exc(), random_id=int(vk_api.utils.get_random_id()))

            # Системные команды
            elif command == "admin":
                try:
                    admins = []
                    if chats.find_one({"chat_id": event.chat_id, "members": {"$elemMatch": {"user_id": {"$eq": event.object.message["from_id"]}, "rank": {"$gt": 0}}}}, {"_id": 0, "members.user_id.$": 1}):
                        users_id = re.findall(r"\[id+(\d+)\|\W*\w+\]", event.object.message["text"])
                        for user in users_id:
                            member = chats.find_one({"chat_id": event.chat_id}, {"_id": 0, "members": {"$elemMatch": {"user_id": {"$eq": int(user)}}}})
                            if member and not member["members"][0]["rank"]:
                                first_name = vk.users.get(user_id=user)[0]["first_name"]
                                chats.update_one({"chat_id": event.chat_id, "members.user_id": int(user)}, {"$set": {"members.$.rank": 1}})
                                admins.append("[id{0}|{1}]".format(str(user), first_name))
                        if admins:
                            vk.messages.send(chat_id=event.chat_id, message="Поздравляем новых админов!!!: " + ', '.join(admins), random_id=int(vk_api.utils.get_random_id()))
                        else:
                            vk.messages.send(chat_id=event.chat_id, message="Похоже, все уже в админах, либо их нет в беседе", random_id=int(vk_api.utils.get_random_id()))
                    else:
                        vk.messages.send(chat_id=event.chat_id, message="У вас нет прав админа или короля", random_id=int(vk_api.utils.get_random_id()))
                except Exception as ex:
                    traceback.print_exc()
                    vk.messages.send(chat_id=event.chat_id, message=traceback.format_exc(), random_id=int(vk_api.utils.get_random_id()))
            elif command == "unadmin":
                try:
                    admins = []
                    if chats.find_one({"chat_id": event.chat_id, "members": {"$elemMatch": {"user_id": {"$eq": event.object.message["from_id"]}, "rank": {"$eq": 2}}}}, {"_id": 0, "members.user_id.$": 1}):
                        users_id = re.findall(r"\[id+(\d+)\|\W*\w+\]", event.object.message["text"])
                        for user in users_id:
                            member = chats.find_one({"chat_id": event.chat_id}, {"_id": 0, "members": {"$elemMatch": {"user_id": {"$eq": int(user)}}}})
                            if member and member["members"][0]["rank"] == 1:
                                first_name = vk.users.get(user_id=user)[0]["first_name"]
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
                    vk.messages.send(chat_id=event.chat_id, message=traceback.format_exc(), random_id=int(vk_api.utils.get_random_id()))
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
                    vk.messages.send(chat_id=event.chat_id, message=traceback.format_exc(), random_id=int(vk_api.utils.get_random_id()))
            # Команды, которые доступны без админки
            if command == "неделя":
                if int(time.strftime("%U", time.gmtime())) % 2 == 0:
                    vk.messages.send(chat_id=event.chat_id, message="НИЖНЯЯ НЕДЕЛЯ", random_id=int(vk_api.utils.get_random_id()))
                else:
                    vk.messages.send(chat_id=event.chat_id, message="ВЕРХНЯЯ НЕДЕЛЯ", random_id=int(vk_api.utils.get_random_id()))

        if re.findall(r"\@(\w+)", event.object.message["text"]):
            pinglist = []
            for ping in re.findall(r"\@(\w+)", event.object.message["text"]):
                user_ids = chats.find_one({"chat_id": event.chat_id, "groups": {"$elemMatch": {"name": {"$eq": ping}}}}, {"_id": 0, "groups.members.$": 1})
                for user_id in user_ids:
                    if user_id not in pinglist:
                        pinglist.append(user_id)
            domains_list = vk.users.get(user_ids=list(pinglist), fields=["domain"])
            domains_dict = {}
            for domain in domains_list:
                domains_dict.update({str(domain["id"]): domain["domain"]})
            if domains_dict:
                vk.messages.send(chat_id=event.chat_id, message="☝☝☝☝☝☝☝☝☝☝\n @" + ' @'.join(list(domains_dict.values())) + "\n☝☝☝☝☝☝☝☝☝☝", random_id=int(vk_api.utils.get_random_id()))