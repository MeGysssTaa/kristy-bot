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

vklong = VkLongPoll(vk_session)
for event in vklong.listen():
    if event.type == VkEventType.MESSAGE_NEW and event.text and event.to_me and event.from_chat:
        if event.text.startswith("!!создать"):
            # print(event.chat_id.self)
            try:
                if event.chat_id not in data:
                    data.update({event.chat_id: {}})
                if event.text.split()[1] in data[event.chat_id]:
                    vk.messages.send(chat_id=event.chat_id, message="Извините-простите, такая группа уже существует(",
                                     random_id=int(vk_api.utils.get_random_id()))
                else:
                    data[event.chat_id].update({event.text.split()[1]: []})
                    vk.messages.send(chat_id=event.chat_id, message="Создала группу: " + event.text.split()[1],
                                     random_id=int(vk_api.utils.get_random_id()))
            except Exception:
                vk.messages.send(chat_id=event.chat_id, message="Что-то пошло не так(((",
                                 random_id=int(vk_api.utils.get_random_id()))
            datafile = open(os.path.dirname(__file__) + os.path.sep + "datakristy.txt", "w+")
            datafile.write(json.dumps(data, indent=4, ensure_ascii=False))
            datafile.close()
        elif event.text.startswith("!!удалить"):
            try:
                if event.chat_id not in data:
                    data.update({event.chat_id: {}})
                if event.text.split()[1] in data[event.chat_id]:
                    data[event.chat_id].pop(event.text.split()[1])
                    vk.messages.send(chat_id=event.chat_id, message="Удалила группу: " + event.text.split()[1],
                                     random_id=int(vk_api.utils.get_random_id()))
                else:
                    vk.messages.send(chat_id=event.chat_id, message="Такой группы нет((",
                                     random_id=int(vk_api.utils.get_random_id()))
            except Exception:
                vk.messages.send(chat_id=event.chat_id, message="Что-то пошло не так(((",
                                 random_id=int(vk_api.utils.get_random_id()))
            datafile = open(os.path.dirname(__file__) + os.path.sep + "datakristy.txt", "w+")
            datafile.write(json.dumps(data, indent=4, ensure_ascii=False))
            datafile.close()
        elif event.text.startswith("!!присоединиться"):
            try:
                if event.chat_id not in data:
                    data.update({event.chat_id: {}})
                if event.text.split()[1] in data[event.chat_id]:
                    userdomain = vk.users.get(user_id=event.user_id, fields=["domain"])[0]["domain"]
                    if userdomain in data[event.chat_id][event.text.split()[1]]:
                        vk.messages.send(chat_id=event.chat_id,
                                         message="Вы уже состоите в группе: " + event.text.split()[1],
                                         random_id=int(vk_api.utils.get_random_id()))
                    else:
                        data[event.chat_id][event.text.split()[1]].append(userdomain)
                        vk.messages.send(chat_id=event.chat_id,
                                         message="Успешно добавила ВАС в группу: " + event.text.split()[1],
                                         random_id=int(vk_api.utils.get_random_id()))
                else:
                    vk.messages.send(chat_id=event.chat_id, message="Такой группы нет((",
                                     random_id=int(vk_api.utils.get_random_id()))
            except Exception as ex:
                print(Exception)
                vk.messages.send(chat_id=event.chat_id, message="Что-то пошло не так(((",
                                 random_id=int(vk_api.utils.get_random_id()))
            datafile = open(os.path.dirname(__file__) + os.path.sep + "datakristy.txt", "w+")
            datafile.write(json.dumps(data, indent=4, ensure_ascii=False))
            datafile.close()
        elif event.text.startswith("!!отключиться"):
            try:
                if event.chat_id not in data:
                    data.update({event.chat_id: {}})
                if event.text.split()[1] in data[event.chat_id]:
                    userdomain = vk.users.get(user_id=event.user_id, fields=["domain"])[0]["domain"]
                    if userdomain in data[event.chat_id][event.text.split()[1]]:
                        data[event.chat_id][event.text.split()[1]].remove(userdomain)
                        vk.messages.send(chat_id=event.chat_id,
                                         message="Успешно отключила ВАС от группы: " + event.text.split()[1],
                                         random_id=int(vk_api.utils.get_random_id()))
                    else:
                        vk.messages.send(chat_id=event.chat_id,
                                         message="Вы не состоите в этой группе: " + event.text.split()[1],
                                         random_id=int(vk_api.utils.get_random_id()))
                else:
                    vk.messages.send(chat_id=event.chat_id, message="Такой группы нет((",
                                     random_id=int(vk_api.utils.get_random_id()))
            except Exception as ex:
                print(Exception)
                vk.messages.send(chat_id=event.chat_id, message="Что-то пошло не так(((",
                                 random_id=int(vk_api.utils.get_random_id()))
            datafile = open(os.path.dirname(__file__) + os.path.sep + "datakristy.txt", "w+")
            datafile.write(json.dumps(data, indent=4, ensure_ascii=False))
            datafile.close()
        elif event.text.startswith("!!пинговать"):
            try:
                if event.chat_id not in data:
                    data.update({event.chat_id: {}})
                if event.text.split()[1] in data[event.chat_id]:
                    ping = ""
                    for user in data[event.chat_id][event.text.split()[1]]:
                        ping += "@" + user + " "
                    if ping:
                        vk.messages.send(chat_id=event.chat_id, message="ПИНГУЮ: " + ping,
                                         random_id=int(vk_api.utils.get_random_id()))
                    else:
                        vk.messages.send(chat_id=event.chat_id,
                                         message="Никого нет в этой группе : " + event.text.split()[1],
                                         random_id=int(vk_api.utils.get_random_id()))
                else:
                    vk.messages.send(chat_id=event.chat_id, message="Такой группы нет((",
                                     random_id=int(vk_api.utils.get_random_id()))
            except Exception as ex:
                print(Exception)
                vk.messages.send(chat_id=event.chat_id, message="Что-то пошло не так(((",
                                 random_id=int(vk_api.utils.get_random_id()))
    elif event.type == VkEventType.MESSAGE_NEW and event.text and event.to_me:
        if event.text == "привет":
            vk.messages.send(user_id=event.user_id,
                             message="привет " + vk.users.get(user_id=event.user_id)[0]["first_name"] + " " +
                                     vk.users.get(user_id=event.user_id)[0]["last_name"],
                             random_id=int(vk_api.utils.get_random_id()))
        elif str(event.text).startswith("!!создать"):
            print(event.user_id)
