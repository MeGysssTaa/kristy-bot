import vk_api, os, time, json
from vk_api.longpoll import VkLongPoll, VkEventType

tokentext = os.environ['VKBOT_TOKEN']

# Для автоматического перезапуска (чтобы GitHub Actions стопил этот процесс и запускал новый при пуше)
pidfile = open(os.path.dirname(__file__) + os.path.sep + 'pid.txt', 'w')
pidfile.write(str(os.getpid()))
pidfile.close()

if not os.path.isfile(os.path.dirname(__file__) + os.path.sep + "datakristy.txt"):
    datafile = open(os.path.dirname(__file__) + os.path.sep + "datakristy.txt", "w+")
    datafile.write("{}")
    datafile.close()

datafile = open(os.path.dirname(__file__) + os.path.sep + "datakristy.txt", "r")
data = json.load(datafile)
datafile.close()

vk_session = vk_api.VkApi(token=tokentext)
vk = vk_session.get_api()

bot_id = vk.users.get()[0]["id"]

vklong = VkLongPoll(vk_session)
for event in vklong.listen():
    # КОГДА ПРИГЛАШАЕШЬ БОТА
    if event.type == VkEventType.CHAT_UPDATE and event.type_id == 6 and event.info["user_id"] == bot_id:
        if str(event.chat_id) not in data:
            data.update({str(event.chat_id): {"admins": [], "members": {}, "groups": {}, "infogroups": {}}})
        data[str(event.chat_id)]["members"].clear()
        info = vk.messages.getConversationMembers(peer_id=(2000000000 + event.chat_id), fields=["domain"])
        print(info)
        for item in info["items"]:
            if item["member_id"] == bot_id:
                userdomain = vk.users.get(user_id=item["invited_by"], fields=["domain"])[0]["domain"]
                if userdomain not in data[str(event.chat_id)]["admins"]:
                    data[str(event.chat_id)]["admins"].append(userdomain)
        for member in info["profiles"]:
            data[str(event.chat_id)]["members"].update({member["id"]: member["domain"]})

        vk.messages.send(chat_id=event.chat_id, message="ПРИВЕТИК", random_id=int(vk_api.utils.get_random_id()))

        datafile = open(os.path.dirname(__file__) + os.path.sep + "datakristy.txt", "w+")
        datafile.write(json.dumps(data, indent=4, ensure_ascii=False))
        datafile.close()

    # ОБРАБОТЧИК СООБЩЕНИЙ В ЧАТЕ
    elif event.type == VkEventType.MESSAGE_NEW and event.text and event.to_me and event.from_chat:
        if event.text.startswith("!создать"):
            try:
                if event.text.split()[1] in data[str(event.chat_id)]["groups"]:
                    vk.messages.send(chat_id=event.chat_id, message="Простите, но данная группа уже существует", random_id=int(vk_api.utils.get_random_id()))
                else:
                    data[str(event.chat_id)]["groups"].update({event.text.split()[1]: []})
                    vk.messages.send(chat_id=event.chat_id, message="Создала группу: " + event.text.split()[1], random_id=int(vk_api.utils.get_random_id()))

                datafile = open(os.path.dirname(__file__) + os.path.sep + "datakristy.txt", "w+")
                datafile.write(json.dumps(data, indent=4, ensure_ascii=False))
                datafile.close()
            except Exception:
                vk.messages.send(chat_id=event.chat_id, message="Что-то пошло не так(((", random_id=int(vk_api.utils.get_random_id()))

        elif event.text.startswith("!удалить"):
            try:
                if event.text.split()[1] in data[str(event.chat_id)]["groups"]:
                    data[str(event.chat_id)]["groups"].pop(event.text.split()[1])
                    vk.messages.send(chat_id=event.chat_id, message="Удалила группу: " + event.text.split()[1], random_id=int(vk_api.utils.get_random_id()))
                else:
                    vk.messages.send(chat_id=event.chat_id, message="Такой группы нет: " + + event.text.split()[1], random_id=int(vk_api.utils.get_random_id()))

                datafile = open(os.path.dirname(__file__) + os.path.sep + "datakristy.txt", "w+")
                datafile.write(json.dumps(data, indent=4, ensure_ascii=False))
                datafile.close()
            except Exception:
                vk.messages.send(chat_id=event.chat_id, message="Что-то пошло не так(((", random_id=int(vk_api.utils.get_random_id()))

        elif event.text.startswith("!присоединиться"):
            try:
                groups_off = []
                groups_on = []
                groups_error = []
                for group in event.text.split(" ", maxsplit=1)[1].split():
                    if group in data[str(event.chat_id)]["groups"]:
                        userdomain = vk.users.get(user_id=event.user_id, fields=["domain"])[0]["domain"]
                        if userdomain in data[str(event.chat_id)]["groups"][group]:
                            groups_on.append(group)
                        else:
                            data[str(event.chat_id)]["groups"][group].append(userdomain)
                            groups_off.append(group)
                    else:
                        groups_error.append(group)

                answer = "Успешно добавила вас в группы: " + ', '.join(groups_off) + "\n"
                answer += "Вы уже состоите в группах: " + ', '.join(groups_on) + "\n"
                answer += "Таких групп нет: " + ', '.join(groups_error)

                datafile = open(os.path.dirname(__file__) + os.path.sep + "datakristy.txt", "w+")
                datafile.write(json.dumps(data, indent=4, ensure_ascii=False))
                datafile.close()

                vk.messages.send(chat_id=event.chat_id, message=answer, random_id=int(vk_api.utils.get_random_id()))
            except Exception as ex:
                print(ex)
                vk.messages.send(chat_id=event.chat_id, message="Что-то пошло не так(((", random_id=int(vk_api.utils.get_random_id()))
        elif event.text.startswith("!отключиться"):
            try:
                groups_on = []
                groups_off = []
                groups_error = []
                for group in event.text.split(" ", maxsplit=1)[1].split():
                    if group in data[str(event.chat_id)]["groups"]:
                        userdomain = vk.users.get(user_id=event.user_id, fields=["domain"])[0]["domain"]
                        if userdomain in data[str(event.chat_id)]["groups"][group]:
                            data[event.chat_id][event.text.split()[1]].remove(userdomain)
                            groups_on.append(group)
                        else:
                            groups_off.append(group)
                    else:
                        groups_error.append(group)
                answer = "Успешно отключила вас от групп: " + ', '.join(groups_on) + "\n"
                answer += "Вы не состоите в группах: " + ', '.join(groups_off) + "\n"
                answer += "Таких групп нет: " + ', '.join(groups_error)

                datafile = open(os.path.dirname(__file__) + os.path.sep + "datakristy.txt", "w+")
                datafile.write(json.dumps(data, indent=4, ensure_ascii=False))
                datafile.close()

                vk.messages.send(chat_id=event.chat_id, message=answer, random_id=int(vk_api.utils.get_random_id()))
            except Exception as ex:
                print(ex)
                vk.messages.send(chat_id=event.chat_id, message="Что-то пошло не так(((", random_id=int(vk_api.utils.get_random_id()))

        elif len(event.text.split('@')) > 1:
            pinglist = event.text.split('@')
            pinglist.pop(0)
            ping = []
            for pinggroup in pinglist:
                if pinggroup.split()[0] in data[str(event.chat_id)]["groups"]:
                    for user in data[str(event.chat_id)]["groups"][pinggroup.split()[0]]:
                        if user not in ping:
                            ping.append(user)
            if ping:
                pingtext = "@" + " @".join(ping)
                vk.messages.send(chat_id=event.chat_id, message=pingtext, random_id=int(vk_api.utils.get_random_id()))
        elif event.text.startswith("!админ"):
            admins_off = []
            admins_on = []
            admins_error = []
            if data[str(event.chat_id)]["members"][str(event.user_id)] in data[str(event.chat_id)]["admins"]:
                for admin in event.text.split(" ", maxsplit=1)[1].split():
                    if admin in data[str(event.chat_id)]["members"].values():
                        if admin not in data[str(event.chat_id)]["admins"]:
                            data[str(event.chat_id)]["admins"].append(admin)
                            admins_off.append(admin)
                        else:
                            admins_on.append(admin)
                    else:
                        admins_error.append(admin)
                answer = "Добавлены админы: " + ', '.join(admins_off) + "\n"
                answer += "Уже состоят в админах: " + ', '.join(admins_on) + "\n"
                answer += "Таких пользователей нет в беседе: " + ', '.join(admins_error)

                datafile = open(os.path.dirname(__file__) + os.path.sep + "datakristy.txt", "w+")
                datafile.write(json.dumps(data, indent=4, ensure_ascii=False))
                datafile.close()

                vk.messages.send(chat_id=event.chat_id, message=answer, random_id=int(vk_api.utils.get_random_id()))
            else:
                vk.messages.send(chat_id=event.chat_id, message="У вас нет прав админа", random_id=int(vk_api.utils.get_random_id()))
            # except Exception as ex:
            # print(ex)
            # vk.messages.send(chat_id = event.chat_id, message = "Что-то пошло не так(((", random_id = int(vk_api.utils.get_random_id()))
        elif event.text.startswith("!неделя"):
            if int(time.strftime("%U", time.gmtime())) % 2 == 0:
                vk.messages.send(chat_id=event.chat_id, message="НИЖНЯЯ НЕДЕЛЯ", random_id=int(vk_api.utils.get_random_id()))
            else:
                vk.messages.send(chat_id=event.chat_id, message="ВЕРХНЯЯ НЕДЕЛЯ", random_id=int(vk_api.utils.get_random_id()))
    elif event.type == VkEventType.MESSAGE_NEW and event.text and event.to_me:
        if event.text == "привет":
            vk.messages.send(user_id=event.user_id, message="привет " + vk.users.get(user_id=event.user_id)[0]["first_name"] + " " + vk.users.get(user_id=event.user_id)[0]["last_name"], random_id=int(vk_api.utils.get_random_id()))
        elif str(event.text).startswith("!!создать"):
            print(event.user_id)
            # vk.messages.send(chat_id = event.chat_id, message = "минет", random_id = int(vk_api.utils.get_random_id()))

