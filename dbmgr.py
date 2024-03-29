import os
from typing import Optional

import pymongo
from datetime import *
import log_util
import ranks

# Максимальное число событий в каждом теге почты бесед. Должно быть кратко шести.
MAX_EVENTS = 48


class DatabaseManager:
    def __init__(self, kristy):
        self.logger = log_util.init_logging(__name__)
        self.kristy = kristy

        self.logger.info('Подключение к базе данных...')
        self.client = pymongo.MongoClient(os.environ['MONGO_HOST'], int(os.environ['MONGO_PORT']))
        self.db = self.client.kristybot
        self.chats = self.db.chats
        self.logger.info('Соединение с базой данных успешно установлено')

    def get_user_groups(self, chat, user):
        """
        Возвращает список названий групп, в которых состоит указанный пользователь ВК в указанной беседе.
        Если указанный пользователь не состоит ни в одной из групп в указанной беседе, возвращает пустой список.
        """
        user_groups = list(self.chats.aggregate([
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

        return list(user_groups[0]['groups']).copy() if user_groups else []

    def get_all_groups(self, chat):
        """
        Возвращает список названий всех групп в указанной беседе.
        """
        all_groups = list(self.chats.distinct(
            "groups.name",
            {
                "chat_id": chat
            }
        ))

        return all_groups

    def pings_str(self, chat, groups, sender=None):
        """
        Возвращает строку, которую можно отправить в указанную беседу, чтобы пингануть (упомянуть)
        участников беседы, которые состоят в указанной группе. sender (того, кто пинганул) можно
        не указывать, если пинговать будет сам бот.
        """
        ping_list = []

        for group in groups:
            users = self.get_group_members(chat, group)

            for user in users:
                if user not in ping_list and user != sender:
                    ping_list.append(user)

        users_vk = self.kristy.vk.users.get(user_ids=ping_list)
        response = ''

        for user_vk in users_vk:
            response += '[id{}|{}] '.format(user_vk['id'], user_vk['first_name'])

        return response

    def get_user_rank(self, chat, user):
        """
        Возвращает ранг (название Enum) указанного пользователя в указанной беседе.
        """
        rank_user = self.chats.find_one(
            {"chat_id": chat, "members": {
                "$elemMatch": {
                    "user_id": {"$eq": user}
                }}
             },
            {"_id": 0, "members.rank.$": 1}
        )

        return rank_user["members"][0]["rank"] if rank_user else ''

    def get_user_rank_val(self, chat, user):
        """
         Возвращает числовое значение ранга (Enum#value) указанного пользователя в указанной беседе.
        """
        return ranks.Rank[self.get_user_rank(chat, user)].value

    def get_user_created_groups(self, chat, user):
        """
        Возвращает список групп, которые создал указанный пользователь в указанной беседе.
        """
        groups_user = list(self.chats.aggregate([
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

    def get_users(self, chat):
        """
        Возвращает ID всех пользователей, состоящих в указанной беседе.
        """
        all_users = list(self.chats.distinct(
            "members.user_id",
            {
                "chat_id": chat
            }
        ))

        return all_users

    def get_last_capy_date(self, chat: int) -> Optional[str]:
        """
        Возвращает дату последней отправки капибары в беседе с указанным ID.
        Если капибары в эту беседу (ещё) не отправлялись, возвращает None.
        """
        result = self.chats.find_one({"chat_id": chat},
                                     {"_id": 0, "last_capy_date": 1})
        return result['last_capy_date'] if result else None

    def set_last_capy_date(self, chat: int, new_date: str):
        """
        Обновляет дату последней отправки капибары в беседе с указанным ID.
        """
        self.logger.debug('Обновлена дата последней отправки капибары в беседе № %s', chat)
        self.chats.update_one({"chat_id": chat},
                              {"$set": {"last_capy_date": new_date}})

    def get_timetable_url(self, chat):
        """
        Возвращает ссылку, по которой можно скачать файл с расписанием беседы с указанным ID.
        Если этой ссылки у данной беседы в БД нет, возвращает None.
        """
        url = self.chats.find_one({"chat_id": chat},
                                  {"_id": 0, "timetable_url": 1})
        return url['timetable_url'] if url else None

    def set_timetable_url(self, chat, new_url):
        """
        Обновляет ссылку, по которой можно скачать файл с расписанием беседы с указанным ID.
        """
        self.logger.debug('Обновлена ссылка на файл с расписанием беседы № %s', chat)
        self.chats.update_one({"chat_id": chat},
                              {"$set": {"timetable_url": new_url}})

    def create_group(self, chat, group_name, creator):
        """
        Создаёт новую группу в указанной беседе от имени указанного пользователя.
        """
        self.logger.debug('Создана группа "%s" в беседе № %s', group_name, chat)
        self.chats.update_one({"chat_id": int(chat)}, {"$push": {
            "groups": {
                "name": group_name,
                "creator": int(creator),
                "members": [],
                "kicked": [],
                "info": ""
            }
        }})

    def delete_group(self, chat, group_name):
        """
        Удаляет группу с указанным названием из указанной беседы.
        """
        self.logger.debug('Удалена группа "%s" в беседе № %s', group_name, chat)
        self.chats.update_one({"chat_id": chat}, {'$pull': {
            "groups": {
                "name": group_name
            }
        }})

    def join_group(self, chat, group_name, user_id):
        """
        Добавляет указанного участника в указанную группу в указанной беседе.
        """
        self.chats.update_one({"chat_id": chat, "groups.name": group_name},
                              {"$push": {
                                  "groups.$.members": user_id
                              }})

    def leave_group(self, chat, group_name, user_id):
        """
        Удаляет указанного участника из указанной группы в указанной беседе.
        """
        self.chats.update_one({"chat_id": chat, "groups.name": group_name},
                              {"$pull": {"groups.$.members": user_id}})

    def rename_group(self, chat, group_name_old, group_name_new):
        """
        Меняет название указанной группы в указанной беседе.
        """
        self.logger.debug('Изменено название группы "%s" на "%s" в беседе № %s',
                          group_name_old, group_name_new, chat)
        self.chats.update_one({"chat_id": chat, "groups.name": group_name_old},
                              {"$set": {"groups.$.name": group_name_new}})

    def all_chat_ids(self):
        """
        Возвращает список численных ID всех бесед, которые есть в БД бота.
        """
        return list(self.chats.distinct("chat_id"))

    def all_chat_names(self):
        """
        Возвращает список названий всех бесед, которые есть в БД бота
        (названия задают администраторы беседы с помощью специальной команды бота).
        """
        return list(self.chats.distinct("name"))

    # todo перенести

    def change_rank(self, chat, user, rank):
        """
        Меняет ранг указанного пользователя в указанной беседе.
        """
        self.chats.update_one({"chat_id": chat, "members.user_id": user},
                              {"$set": {"members.$.rank": rank}})

    def get_attachment(self, chat, tag):
        """
        Возвращает вложения и текст, прикреплённые к указанному тегу ('?tag').
        """
        attachment = self.chats.find_one({"chat_id": chat,
                                          "attachments": {
                                              "$elemMatch": {
                                                  "tag": {"$eq": tag}
                                              }
                                          }},
                                         {"_id": 0,
                                          "attachments.$": 1
                                          })
        return attachment["attachments"][0] if attachment else {}

    def get_tag_attachments(self, chat):
        tags = self.chats.find_one({"chat_id": chat, },
                                   {"_id": 0,
                                    "attachments.tag": 1
                                    })
        return [tag['tag'] for tag in tags["attachments"]] if tags else []

    def add_attachment(self, chat, user, tag, message, attachments):
        """
        Создаёт новое вложение в указанной беседе с указанными тегом, сообщением и, собственно, вложениями.
        """
        self.logger.debug('Создано вложение "%s" в беседе № %s', tag, chat)
        self.chats.update_one({"chat_id": int(chat)}, {"$push": {
            "attachments": {
                "tag": tag,
                "creator": user,
                "message": message,
                "attachments": attachments
            }
        }})

    def edit_attachment(self, chat, tag, message, attachments):
        """
        Изменяет уже существующее вложение в указанной беседе (прикрепляет
        новое сообщение и вложение/вложения к указанному тегу).
        """
        self.logger.debug('Обновлено вложение "%s" в беседе № %s', tag, chat)
        self.chats.update_one({"chat_id": int(chat), "attachments.tag": tag}, {"$set": {
            "attachments.$.message": message,
            "attachments.$.attachments": attachments,
        }})

    def remove_attachment(self, chat, tag):
        """
        Удаляет вложение с указанном тегом из указанной беседы.
        """
        self.logger.debug('Удалено вложение "%s" в беседе № %s', tag, chat)
        self.chats.update_one({"chat_id": chat}, {'$pull': {
            "attachments": {
                "tag": tag
            }
        }})

    def rename_chat(self, chat, name):
        """
        Меняет название указанной беседы в БД бота.
        """
        self.logger.debug('Установлено новое название беседы № %s: "%s"', chat, name)
        self.chats.update_one({"chat_id": chat},
                              {"$set": {"name": name}})

    def get_events_for_email(self, chat, tag):
        """
        Возвращает все события для указанного тега почты в указанной беседе.
        """
        events = self.chats.find_one({"chat_id": chat,
                                      "email": {
                                          "$elemMatch": {
                                              "tag": {"$eq": tag}
                                          }
                                      }},
                                     {"_id": 1,
                                      "email.events.$": 1
                                      })
        return list(events["email"][0]["events"]) if events else []

    def get_event_email(self, chat, tag, event_id):

        events = self.chats.find_one({"chat_id": chat,
                                      },
                                     {"_id": 0,
                                      "email": {
                                          "$elemMatch": {
                                              "tag": tag
                                          }
                                      }
                                      })
        # FIXME запомни сука, я проиграл битву, но не войну
        if events:
            for event in events["email"][0]["events"]:
                if event["id"] == event_id:
                    return event
        return {}

    def all_email_tags(self, chat):
        """
        Возвращает список всех тегов почты, существующих в указанной беседе.
        """
        tags = list(self.chats.distinct(
            "email.tag",
            {
                "chat_id": chat
            }
        ))
        return tags

    def create_event(self, chat, tag, date, message="", attachments=None):
        """
        Создает новое событие для указанного тега в указанной беседе.
        Если событий в этом теге становится больше MAX_EVENTS, то удаляет самое старое событие.
        """
        if attachments is None:
            attachments = []

        events_email = self.get_events_for_email(chat, tag)
        events = sorted(events_email, key=lambda x: x['id'])
        if len(events) == MAX_EVENTS:
            events.pop(0)
        if not events:
            event_id = 1
        else:
            event_id = events[-1]['id'] + 1

        events.append(
            {"id": event_id, "date": date, "message": message, "attachments": attachments})
        self.chats.update_one({"chat_id": chat, "email.tag": tag},
                              {"$set": {"email.$.events": events}})
        return event_id

    def edit_event(self, chat, tag, event_id, date, message="", attachments=None):
        """
        Изменяет данные о событии, привязанном к указанному тегу в указанной беседе.
        """
        if attachments is None:
            attachments = []
        events = self.get_events_for_email(chat, tag)
        for event in events:
            if event['id'] == event_id:
                event["date"] = date
                event["message"] = message
                event["attachments"] = attachments
                self.chats.update_one({"chat_id": chat, "email.tag": tag},
                                      {"$set": {"email.$.events": events}})
                return

    def delete_event(self, chat, tag, event_id):
        self.chats.update_one({"chat_id": chat,
                               "email.tag": tag},
                              {'$pull': {
                                  "email.$.events":
                                      {'id': event_id}
                              }})

    def create_email(self, chat, tag):
        """
        Создаёт новую почту в указанной беседе с указанным тегом.
        """
        self.logger.debug('Создана почта с тегом "%s" в беседе № %s', tag, chat)
        self.chats.update_one({"chat_id": int(chat)}, {"$push": {
            "email": {
                "tag": tag,
                "events": []
            }
        }})

    def delete_email(self, chat, tag):
        """
        Удаляет почту с указанным тегом из указанной беседы.
        """
        self.logger.debug('Удалена почта с тегом "%s" в беседе № %s', tag, chat)
        self.chats.update_one({"chat_id": chat}, {'$pull': {
            "email": {
                "tag": tag
            }
        }})

    def get_user_chats(self, user):
        """
        Возвращает список численных ID бесед из БД бота, в которых состоит указанный пользователь.
        """
        chats_user = list(self.chats.aggregate(
            [{"$match": {
                "$and": [{"members.user_id": user}]
            }}, {"$group": {
                "_id": "1",
                "chats": {
                    "$push": {
                        "chat_id": "$chat_id",
                        "name": "$name"
                    }
                }
            }}, {"$sort": {
                "chat_id": 1
            }}
            ]))
        return chats_user[0]['chats'] if chats_user else []

    def get_group_members(self, chat, group):
        """
        Возвращает список участников указанной группы в указанной беседе.
        """
        members = self.chats.find_one({"chat_id": chat,
                                       "groups": {
                                           "$elemMatch": {
                                               "name": {"$eq": group}
                                           }
                                       }},
                                      {"_id": 0,
                                       "groups.members.$": 1
                                       })
        return members['groups'][0]['members'] if members else []

    def get_chat_name(self, chat):
        """
        Возвращает название беседы с указанным ID в БД бота.
        Если администратор указанной беседы не задал ей названия с помощью специальной команды, возвращает str(chat).
        """
        name = self.chats.find_one({"chat_id": chat},
                                   {"_id": 0, "name": 1})
        return name['name'] if name else str(chat)

    def handle_all_abuse(self, chat, user):
        """
        Фиксирует факт использования указанным пользователем @all или подобного упоминания в указанной беседе
        (увеличивает их счётчик в БД бота на 1).
        """
        self.chats.update_one({"chat_id": chat, "members.user_id": user},
                              {"$inc": {"members.$.all": 1}})

    def add_user_to_chat(self, chat, user):
        """
        Регистрирует указанного пользователя в указанной беседе (новый участник).
        """
        self.chats.update_one({"chat_id": chat, "members.user_id": {"$ne": user}},
                              {"$push": {
                                  "members": {
                                      "user_id": user,
                                      "rank": "USER",
                                      "all": 0
                                  }
                              }})

    def get_all_abusers(self, chat):
        """
        Возвращает список численных ID всех пользователей, у которых счётчик @all и подобных упоминаний
        в указанной беседе превышает 0, т.е. это будет список участников, хоть раз использовавших @all/...
        """
        users = list(self.chats.aggregate([
            {"$unwind": "$members"}, {"$match": {
                "$and": [
                    {"chat_id": int(chat)},
                    {"members.all": {
                        "$gt": 0
                    }}
                ]
            }
            }, {"$group": {
                "_id": "$chat_id",
                "members": {
                    "$push": {"user_id": "$members.user_id", "all": "$members.all"}
                }
            }}
        ]))
        return users[0]["members"] if users else []

    def is_chat_in_db(self, chat_id):
        """
        Проверяет, есть ли беседа с указанным ID в БД бота (True) или нет (False).
        """
        return self.chats.find_one({"chat_id": chat_id})

    def register_chat(self, chat_id, host):
        """
        Добавляет указанную беседу в БД бота. Участнику, который,
        пригласил бота (host), сразу же присваивается ранг KING.
        """
        self.logger.debug('Бот был добавлен в беседу № %s пользователем %s', chat_id, host)
        self.chats.insert_one({"chat_id": chat_id, "name": str(chat_id),
                               "members": [
                                   {
                                       "user_id": host,
                                       "rank": "KING"
                                   }
                               ],
                               "groups": [],
                               "attachments": [],
                               "email": []})

    def voice(self, chat_id, sender, duration):
        self.chats.update_one({"chat_id": chat_id, "members.user_id": sender},
                              {"$inc": {"members.$.voice_duration": duration, "members.$.voice_count": 1}})

    def get_all_voices(self, chat):
        voices = list(self.chats.aggregate([
            {"$unwind": "$members"}, {"$match": {
                "$and": [
                    {"chat_id": int(chat)},
                    {"members.voice_count": {
                        "$gt": 0
                    }}
                ]
            }
            }, {"$group": {
                "_id": "$chat_id",
                "members": {
                    "$push": {"user_id": "$members.user_id", "voice_count": "$members.voice_count",
                              "voice_duration": "$members.voice_duration"}
                }
            }}
        ]))
        return voices[0]["members"] if voices else []

    def get_object_all_groups(self, chat):
        groups = list(self.chats.distinct(
            "groups",
            {
                "chat_id": chat
            }
        ))
        return groups

    def get_future_events_email(self, chat, tag):
        events_dt = self.chats.find_one({"chat_id": chat,
                                         "email": {
                                             "$elemMatch": {
                                                 "tag": {"$eq": tag}
                                             }
                                         }},
                                        {"_id": 0,
                                         "email.events.$": 1
                                         })
        zone = timedelta(hours=2)
        print(events_dt)
        return [event for event in events_dt["email"][0]["events"] if
                event["date"] > datetime.utcnow() + zone] if events_dt else []

    def get_events_with_date(self, chat, tag, date_time, time_to):
        events_dt = self.chats.find_one({"chat_id": chat,
                                         "email": {
                                             "$elemMatch": {
                                                 "tag": {"$eq": tag}
                                             }
                                         }},
                                        {"_id": 0,
                                         "email.events.$": 1
                                         })
        return [event for event in events_dt["email"][0]["events"] if
                event["date"] == date_time + timedelta(hours=time_to)] if events_dt else []

    def add_new_random_voice(self, chat, user_id, voice_id):
        self.chats.update_one({"chat_id": chat},
                              {"$push": {
                                  f"voices.{user_id}": voice_id
                              }})

    def get_all_random_voices(self, chat):
        voices = self.chats.find_one(
            {
                "chat_id": chat
            },
            {"voices": 1}

        )
        return voices["voices"] if voices and "voices" in voices else {}

    def delete_all_voices(self, chat):
        self.chats.update_one({"chat_id": chat}, {'$unset': {"voices": 1}})

    def get_new_message_chat(self, chat):
        new_message = self.chats.find_one({"chat_id": chat},
                                          {"_id": 0, "actions.new": 1})
        return new_message['actions']['new'] if new_message else ''

    def get_invite_message_chat(self, chat):
        invite_message = self.chats.find_one({"chat_id": chat},
                                             {"_id": 0, "actions.invite": 1})
        return invite_message['actions']['invite'] if invite_message else ''

    def get_return_message_chat(self, chat):
        return_message = self.chats.find_one({"chat_id": chat},
                                             {"_id": 0, "actions.return": 1})
        return return_message['actions']['return'] if return_message else ''

    def get_leave_message_chat(self, chat):
        leave_message = self.chats.find_one({"chat_id": chat},
                                            {"_id": 0, "actions.leave": 1})
        return leave_message['actions']['leave'] if leave_message else ''

    def get_kick_message_chat(self, chat):
        kick_message = self.chats.find_one({"chat_id": chat},
                                           {"_id": 0, "actions.kick": 1})
        return kick_message['actions']['leave'] if kick_message else ''

    def check_new_year(self, chat, user):
        rank_user = self.chats.find_one(
            {"chat_id": chat, "members": {
                "$elemMatch": {
                    "user_id": user}
            }
             },
            {"_id": 0, "members.$": 1}
        )
        return 'new_year' in rank_user["members"][0]

    def get_members_new_year(self, chat):
        members = list(self.chats.aggregate([
            {"$unwind": "$members"}, {"$match": {
                "$and": [
                    {"chat_id": chat},
                    {"members.new_year": {
                        "$eq": True
                    }}
                ]
            }
            }, {"$group": {
                "_id": "$chat_id",
                "members": {
                    "$push": {"user_id": "$members.user_id"}
                }
            }}
        ]))
        return members[0]["members"] if members else []

    def set_new_year(self, chat, user):
        self.chats.update_one({"chat_id": chat, "members.user_id": user},
                              {"$set": {"members.$.new_year": True}})
        pass
