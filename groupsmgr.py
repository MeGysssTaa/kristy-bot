def get_groups(chats_db, chat_id, user_id):
    """
    Возвращает список названий групп, в которых состоит указанный пользователь ВК в указанной беседе.

    :param chats_db: База данных бота.
    :param chat_id: ID беседы (может быть как str, так и int).
    :param user_id: ID пользователя (может быть как str, так и int).

    :return: список названий групп (список str), в которых состоит указанный пользователь ВК в указанной беседе.
             Если указанный пользователь не состоит ни в одной из групп в указанной беседе, возвращает пустой список.
    """
    all_user_groups = list(chats_db.aggregate([
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
    ]
    ))

    groups = []

    if len(all_user_groups) > 0:
        for i in range(len(all_user_groups[0]['groups'])):
            groups.append(all_user_groups[0]['groups'][i])

    return groups
