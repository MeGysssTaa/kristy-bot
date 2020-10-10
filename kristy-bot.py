import vk_api, os, time, json, pymysql, re
from vk_api.longpoll import VkLongPoll, VkEventType


def downloads():
    global data
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


def update_chat(chat_id):
    info = vk.messages.getConversationMembers(peer_id=(2000000000 + event.chat_id), fields=["domain"])
    print(info)
    data["chats"][str(event.chat_id)]["members"].clear()
    if not data["chats"][str(event.chat_id)]["king"]:
        for item in info["items"]:
            if item["member_id"] == bot_id:
                data["chats"][str(event.chat_id)]["king"] = str(item["invited_by"])
                break
    for member in info["profiles"]:
        data["chats"][str(event.chat_id)]["members"].update({member["id"]: member["domain"]})


downloads()

tokentext = os.environ['VKBOT_TOKEN']
vk_session = vk_api.VkApi(token=tokentext)
vk = vk_session.get_api()
bot_id = vk.users.get()[0]["id"]

vklong = VkLongPoll(vk_session)
for event in vklong.listen():

    # КОГДА ПРИГЛАШАЕШЬ БОТА
    if event.type == VkEventType.CHAT_UPDATE and event.type_id == 6 and event.info["user_id"] == bot_id:
        if str(event.chat_id) not in data:
            data.update({"chats": {str(event.chat_id): {"king": "", "admins": [], "members": {}, "groups": {}, "infogroups": {}}}})

        update_chat(event.chat_id)

        vk.messages.send(chat_id=event.chat_id, message="Я загрузила все данные и готова к бою!", random_id=int(vk_api.utils.get_random_id()))

        datafile = open(os.path.dirname(__file__) + os.path.sep + "datakristy.txt", "w+")
        datafile.write(json.dumps(data, indent=4, ensure_ascii=False))
        datafile.close()

    # ОБРАБОТЧИК СООБЩЕНИЙ В ЧАТЕ
    elif event.type == VkEventType.MESSAGE_NEW and event.text and event.to_me and event.from_chat:
        if event.text.startswith("!создать"):
            try:
                groups_off = []
                groups_on = []
                for group in event.text.split(" ", maxsplit=1)[1].split():
                    if group in data["chats"][str(event.chat_id)]["groups"]:
                        groups_on.append(group)
                    else:
                        data["chats"][str(event.chat_id)]["groups"].update({group: {"сreator": str(event.user_id), "members": [], "info": ""}})
                        groups_off.append(group)

                if not groups_on:
                    vk.messages.send(chat_id=event.chat_id, message="Я добавила все ниже перечисленные группы:\n➕ " + '\n➕ '.join(groups_off), random_id=int(vk_api.utils.get_random_id()))
                else:
                    if not groups_off:
                        vk.messages.send(chat_id=event.chat_id, message="Все группы и так уже добавлены:\n✔ " + '\n✔ '.join(groups_on), random_id=int(vk_api.utils.get_random_id()))
                    else:
                        vk.messages.send(chat_id=event.chat_id, message="Я добавила все нижеперечисленные группы:\n➕ " + '\n➕ '.join(groups_off)
                                                                        + "\nНо также некоторые группы уже были добавлены ранее:\n✔ " + '\n✔ '.join(groups_on), random_id=int(vk_api.utils.get_random_id()))

                datafile = open(os.path.dirname(__file__) + os.path.sep + "datakristy.txt", "w+")
                datafile.write(json.dumps(data, indent=4, ensure_ascii=False))
                datafile.close()
            except Exception as ex:
                print(ex)
                vk.messages.send(chat_id=event.chat_id, message="Что-то пошло не так(((", random_id=int(vk_api.utils.get_random_id()))

        elif event.text.startswith("!удалить"):
            try:
                groups_on = []
                groups_off = []
                groups_error = []
                for group in event.text.split(" ", maxsplit=1)[1].split():
                    if group in data["chats"][str(event.chat_id)]["groups"]:
                        if event.user_id in data["chats"][str(event.chat_id)]["groups"]["creator"]:
                            groups_on.append(group)
                            data["chats"][str(event.chat_id)]["groups"].remove(group)
                        else:
                            groups_error.append(group)
                    else:
                        groups_off.append(group)

                vk.messages.send(chat_id=event.chat_id, message="Ниже перечисленны группы, которые вы успешно удалили:\n✖ " + '\n✖ '.join(groups_on)
                                                                + "\nТакже перечислены группы, которых нет в беседе:\n✖ " + '\n✖ '.join(groups_off)
                                                                + "\nА также группы, которые вы не создавали и не можете удалить:\n✖ " + '\n✖ '.join(groups_error), random_id=int(vk_api.utils.get_random_id()))

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
                    if group in data["chats"][str(event.chat_id)]["groups"]:
                        if str(event.user_id) in data["chats"][str(event.chat_id)]["groups"][group]["members"]:
                            groups_on.append(group)
                        else:
                            data["chats"][str(event.chat_id)]["groups"][group]["members"].append(str(event.user_id))
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
                    if group in data["chats"][str(event.chat_id)]["groups"]:
                        if str(event.user_id) in data["chats"][str(event.chat_id)]["groups"][group]["members"]:
                            data["chats"][str(event.chat_id)]["groups"][group]["members"].remove(str(event.user_id))
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

        # countdog = re.findall(r"\[(\w+\|\W*\w+)\]", event.text)
        if re.findall(r"\@(\S+)", event.text):
            pinglist = []
            for ping in re.findall(r"\@(\S+)", event.text):
                if ping in data["chats"][str(event.chat_id)]["groups"]:
                    for member in data["chats"][str(event.chat_id)]["groups"][ping]["members"]:
                        if not data["chats"][str(event.chat_id)]["members"][member] in pinglist:
                            pinglist.append(data["chats"][str(event.chat_id)]["members"][member])
            if pinglist:
                vk.messages.send(chat_id=event.chat_id, message="@" + ' @'.join(pinglist), random_id=int(vk_api.utils.get_random_id()))
        if event.text.startswith("!админ"):
            try:
                admins_off = []
                admins_on = []
                admins_error = []
                if str(event.user_id) in data["chats"][str(event.chat_id)]["admins"] or str(event.user_id) in data["chats"][str(event.chat_id)]["king"]:
                    for admin in re.findall(r"\[[A-Za-z]+(\d+)\|\W*\w+\]", event.text):
                        if admin in data["chats"][str(event.chat_id)]["members"]:
                            if admin not in data["chats"][str(event.chat_id)]["admins"]:
                                data["chats"][str(event.chat_id)]["admins"].append(admin)
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
            except Exception as ex:
                print(ex)
                vk.messages.send(chat_id=event.chat_id, message="Что-то пошло не так(((", random_id=int(vk_api.utils.get_random_id()))
        elif event.text.startswith("!unадмин"):
            try:
                admins_off = []
                admins_on = []
                admins_error = []
                if str(event.user_id) in data["chats"][str(event.chat_id)]["king"]:
                    for admin in re.findall(r"\[[A-Za-z]+(\d+)\|\W*\w+\]", event.text):
                        if admin in data["chats"][str(event.chat_id)]["members"]:
                            if admin in data["chats"][str(event.chat_id)]["admins"]:
                                data["chats"][str(event.chat_id)]["admins"].remove(admin)
                                admins_on.append(admin)
                            else:
                                admins_off.append(admin)
                        else:
                            admins_error.append(admin)
                    answer = "Забраны админки: " + ', '.join(admins_on) + "\n"
                    answer += "Нету в админках" + ', '.join(admins_off) + "\n"
                    answer += "Таких пользователей нет в беседе: " + ', '.join(admins_error)

                    datafile = open(os.path.dirname(__file__) + os.path.sep + "datakristy.txt", "w+")
                    datafile.write(json.dumps(data, indent=4, ensure_ascii=False))
                    datafile.close()

                    vk.messages.send(chat_id=event.chat_id, message=answer, random_id=int(vk_api.utils.get_random_id()))
                else:
                    vk.messages.send(chat_id=event.chat_id, message="У вас нет прав админа", random_id=int(vk_api.utils.get_random_id()))
            except Exception as ex:
                print(ex)
                vk.messages.send(chat_id=event.chat_id, message="Что-то пошло не так(((", random_id=int(vk_api.utils.get_random_id()))
        elif event.text.startswith("!неделя"):
            if int(time.strftime("%U", time.gmtime())) % 2 == 0:
                vk.messages.send(chat_id=event.chat_id, message="НИЖНЯЯ НЕДЕЛЯ", random_id=int(vk_api.utils.get_random_id()))
            else:
                vk.messages.send(chat_id=event.chat_id, message="ВЕРХНЯЯ НЕДЕЛЯ", random_id=int(vk_api.utils.get_random_id()))
        elif event.text.startswith("!deldata"):
            datafile = open(os.path.dirname(__file__) + os.path.sep + "datakristy.txt", "w+")
            datafile.write("{}")
            datafile.close()
            vk.messages.send(chat_id=event.chat_id, message="Ты чево наделал.....", random_id=int(vk_api.utils.get_random_id()))

    elif event.type == VkEventType.MESSAGE_NEW and event.text and event.to_me:
        if event.text == "привет":
            vk.messages.send(user_id=event.user_id, message="привет " + vk.users.get(user_id=event.user_id)[0]["first_name"] + " " + vk.users.get(user_id=event.user_id)[0]["last_name"], random_id=int(vk_api.utils.get_random_id()))
        elif str(event.text).startswith("!!создать"):
            print(event.user_id)
            # vk.messages.send(chat_id = event.chat_id, message = "минет", random_id = int(vk_api.utils.get_random_id()))


