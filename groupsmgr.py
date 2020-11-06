def get_groups(chats, chat_id, user_id):
    """
    Возвращает список названий групп, в которых состоит указанный пользователь ВК в указанной беседе.

    :param chats: БД бота.
    :param chat_id: ID беседы (может быть как str, так и int).
    :param user_id: ID пользователя (может быть как str, так и int).

    :return: список названий групп (список str), в которых состоит указанный пользователь ВК в указанной беседе.
             Если указанный пользователь не состоит ни в одной из групп в указанной беседе, возвращает пустой список.
    """
    print('get_groups 1')
    print('get_groups 2')

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

    print('get_groups 3')

    return list(all_user_groups[0]['groups']).copy() if all_user_groups else []


def create_group(chat, group_name, creator):
    """
    Создаёт новую группу.

    :param chat: ID беседы (может быть как str, так и int), в которой нужно создать эту группу.
    :param group_name: Название группы.
    :param creator: ID оздателя группы (может быть как str, так и int).
    """
    from kristybot import chats

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
