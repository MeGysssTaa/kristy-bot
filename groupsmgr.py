import kristybot


def ff_get_groups(chat_id, user_id):
    """
    Возвращает список названий групп, в которых состоит указанный пользователь ВК в указанной беседе.

    :param chat_id: ID беседы (может быть как str, так и int).
    :param user_id: ID пользователя (может быть как str, так и int).

    :return: список названий групп (список str), в которых состоит указанный пользователь ВК в указанной беседе.
             Если указанный пользователь не состоит ни в одной из групп в указанной беседе, возвращает пустой список.
    """
    all_user_groups = list(kristybot.chats.aggregate([
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


def create_group(chat, group_name, creator):
    """
    Создаёт новую группу.

    :param chat: ID беседы (может быть как str, так и int), в которой нужно создать эту группу.
    :param group_name: Название группы.
    :param creator: ID оздателя группы (может быть как str, так и int).
    """
    kristybot.chats.update_one({"chat_id": int(chat)}, {"$push": {
        "groups": {
            "name": group_name,
            "creator": int(creator),
            "members": [],
            "kicked": [],
            "email": [],  # здесь будем хранить дз для каждой группы
            "info": ""
        }
    }})
