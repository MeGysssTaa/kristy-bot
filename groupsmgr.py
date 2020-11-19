from kristybot import GetChatsDB

chats = GetChatsDB()


def get_user_groups(chat, user):
    """
    Возвращает список названий групп, в которых состоит указанный пользователь ВК в указанной беседе.

    :param chat: ID беседы (может быть как str, так и int).
    :param user: ID пользователя (может быть как str, так и int).

    :return: список названий групп (список str), в которых состоит указанный пользователь ВК в указанной беседе.
             Если указанный пользователь не состоит ни в одной из групп в указанной беседе, возвращает пустой список.
    """
    all_user_groups = list(chats.aggregate([
        {"$unwind": "$groups"}, {"$match": {
            "$and": [
                {"chat_id": int(chat)},
                {"groups.members": {
                    "$eq": int(user)
                }}
            ]
        }
        }, {"$group": {
            "_id": "$chat_id",
            "groups": {
                "$push": "$groups.name"
            }
        }}
    ]))

    return list(all_user_groups[0]['groups']).copy() if all_user_groups else []


def get_all_groups(chat):
    """
    Возвращает список названий всех групп в чате.

    :param chat: ID беседы (может быть как str, так и int).

    :return: список названий групп (список str), в которых состоит указанный пользователь ВК в указанной беседе.
             Если указанный пользователь не состоит ни в одной из групп в указанной беседе, возвращает пустой список.
    """  # TODO переименовать return
    all_groups = list(chats.distinct(
        "groups.name",
        {
            "chat_id": chat
        }
    ))

    return all_groups


def get_rank_user(chat, user):
    """
    получить ранг
    """
    rank_user = chats.find_one(
        {"chat_id": chat, "members": {
            "$elemMatch": {
                "user_id": {"$eq": user}
            }}
         },
        {"_id": 0, "members.rank.$": 1}
    )

    return rank_user["members"][0]["rank"]


def get_groups_created_user(chat, user):
    """
    возвращает список групп, которые пользователь создал
    """
    groups_user = list(chats.aggregate([
        {"$unwind": "$groups"}, {"$match": {
            "$and": [
                {"chat_id": chat},
                {"groups.creator": {"$eq": user}}
            ]}},
        {"$group": {
            "_id": "$chat_id",
            "groups": {
                "$push": "$groups.name"
            }}}]))

    return list(groups_user[0]["groups"]).copy() if groups_user else []


def get_all_users(chat):
    """
    получить всех пользователей в чате
    """
    all_users = list(chats.distinct(
        "members.user_id",
        {
            "chat_id": chat
        }
    ))

    return all_users


def create_group(chat, group_name, creator):
    """
    Создаёт новую группу.

    :param chat: ID беседы (может быть как str, так и int), в которой нужно создать эту группу.
    :param group_name: Название группы.
    :param creator: ID оздателя группы (может быть как str, так и int).
    """
    chats.update_one({"chat_id": int(chat)}, {"$push": {
        "groups": {
            "name": group_name,
            "creator": int(creator),
            "members": [],
            "kicked": [],
            "info": ""
        }
    }})


def delete_group(chat, group_name):
    """
    удаляет группу
    """
    chats.update_one({"chat_id": chat}, {'$pull': {
        "groups": {
            "name": group_name
        }
    }})


def join_group(chat, group_name, user_id):
    """
    добавляет в группу участника
    """
    chats.update_one({"chat_id": chat, "groups.name": group_name},
                     {"$push": {
                         "groups.$.members": user_id
                     }})


def left_group(chat, group_name, user_id):
    """
    удаляет из группы участница
    """
    chats.update_one({"chat_id": chat, "groups.name": group_name},
                     {"$pull": {"groups.$.members": user_id}})


def rename_group(chat, group_name_old, group_name_new):
    """
    переименовать группу
    """
    chats.update_one({"chat_id": chat, "groups.name": group_name_old},
                     {"$set": {"groups.$.name": group_name_new}})


def get_all_chats():
    """
    Ищет беседы, которые есть в БД бота.
    :return: список численных ID всех бесед, которые есть в БД бота.
    """
    chat_objects = list(chats.find({}, {"chat_id": 1, "_id": 0}))  # не включаем _id в вывод (по умолчанию он там)
    return (int(chat_obj['chat_id']) for chat_obj in chat_objects)  # преобразуем в список (генератор) int


def get_attachment(chat, tag):
    """
    получаем вложения + текст для префикса ?.
    """
    attachment = chats.find_one({"chat_id": chat,
                                 "attachments": {
                                     "$elemMatch": {
                                         "tag": {"$eq": tag}
                                     }
                                 }},
                                {"_id": 0,
                                 "attachments": 1
                                 })
    return attachment["attachments"][0] if attachment else {}

def change_rank(chat, user, rank):
    """

    """
    chats.update_one({"chat_id": chat, "members.user_id": user},
                     {"$set": {"members.$.rank": rank}})

def add_attachment(chat, tag, message, attachments):
    """
    """
    chats.update_one({"chat_id": int(chat)}, {"$push": {
        "attachments": {
            "tag": tag,
            "message": message,
            "attachments": attachments
        }
    }})
