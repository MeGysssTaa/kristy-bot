from kristybot import GetChatsBD

chats = GetChatsBD()
print(chats)


def get_groups(chat_id, user_id):
    """
    Возвращает список названий групп, в которых состоит указанный пользователь ВК в указанной беседе.

    :param chats: БД бота.
    :param chat_id: ID беседы (может быть как str, так и int).
    :param user_id: ID пользователя (может быть как str, так и int).

    :return: список названий групп (список str), в которых состоит указанный пользователь ВК в указанной беседе.
             Если указанный пользователь не состоит ни в одной из групп в указанной беседе, возвращает пустой список.
    """
    all_user_groups = list(chats.aggregate([
        {"$unwind": "$groups"}, {"$match": {
            "$and": [
                {"chat_id": int(chat_id)},
                {"groups.members": {
                    "$eq": int(user_id)
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


def get_all_groups(chat_id):
    """
    Возвращает список названий всех групп в чате.

    :param chats: БД бота.
    :param chat_id: ID беседы (может быть как str, так и int).

    :return: список названий групп (список str), в которых состоит указанный пользователь ВК в указанной беседе.
             Если указанный пользователь не состоит ни в одной из групп в указанной беседе, возвращает пустой список.
    """  # TODO переименовать return
    all_groups = list(chats.distinct(
        "groups.name",
        {
            "chat_id": chat_id
        }
    ))

    return all_groups


def get_rank_user(chat_id, user_id):
    """
    """
    rank_user = chats.find_one(
        {"chat_id": chat_id, "members": {
            "$elemMatch": {
                "user_id": {"$eq": user_id}
            }}
         },
        {"_id": 0, "members.rank.$": 1}
    )

    return int(rank_user["members"][0]["rank"])


def get_groups_created_user(chat_id, user_id):
    """
    возвращает список групп, которые пользователь создал
    """
    # TODO короче вот здесь снизу норм оформи, я пытался, не получается
    groups_user = list(chats.aggregate([
        {"$unwind": "$groups"}, {"$match": {
            "$and": [
                {"chat_id": chat_id},
                {"groups.creator": {"$eq": user_id}}
            ]}},
        {"$group": {
            "_id": "$chat_id",
            "groups": {
                "$push": "$groups.name"
            }}}]))

    return list(groups_user[0]["groups"]).copy() if groups_user else []


def create_group(chat, group_name, creator):
    """
    Создаёт новую группу.

    :param chats: БД бота.
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
            "email": [],  # здесь будем хранить дз для каждой группы
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


def connect_group(chat, group_name, user_id):
    """
    добавляет в группу участника
    """
    # TODO тоже красиво сделать
    chats.update_one({"chat_id": chat, "groups.name": group_name},
                     {"$push": {"groups.$.members": user_id}})
