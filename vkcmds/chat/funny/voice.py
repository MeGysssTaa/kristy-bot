import ranks
import keyboards
from vkcommands import VKCommand


class ChooseChat(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='голосовые',
                           desc='Показывает топ 5 по голосовым и их среднее время')

    def execute(self, chat, peer, sender, args=None, attachments=None, fwd_messages=None):
        print(1)
        voices = self.kristy.db.get_all_voices(chat)
        if not voices:
            self.kristy.send(peer, "Никто ещё не записывал голосовые")
            return
        voices_new = sorted(voices, key=lambda voice: voice["voice_count"], reverse=True)
        dict_ids = {}
        for number, voice in enumerate(voices_new):
            if number == 5:
                break
            dict_ids.update({voice["user_id"]: [voice["voice_count"], voice["voice_duration"]]})
        users_vk = self.kristy.vk.users.get(user_ids=list(dict_ids.keys()))
        response = "Топ 5 по количеству голосовых: \n"
        for number, user in enumerate(users_vk):
            response += str(number + 1) + ". {0} {1}: {2} (📈 ≈ {3} c., ⌛".format(
                user['first_name'], user['last_name'], str(dict_ids[user['id']][0]), str('{:.2g}'.format(dict_ids[user['id']][1] / dict_ids[user['id']][0])))
            if dict_ids[user['id']][1] // 86400 > 0:
                response += ' ' + str(dict_ids[user['id']][1] // 86400) + ' дн.'
            if dict_ids[user['id']][1] % 86400 // 3600 > 0:
                response += ' ' + str(dict_ids[user['id']][1] % 86400 // 3600) + ' ч.'
            if dict_ids[user['id']][1] % 3600 // 60 > 0:
                response += ' ' + str(dict_ids[user['id']][1] % 3600 // 60) + ' м.'
            if dict_ids[user['id']][1] % 60 > 0:
                response += ' ' + str(dict_ids[user['id']][1] % 60) + ' с.'
            response += ') \n'
        voices_new = sorted(voices, key=lambda voice: voice["voice_duration"], reverse=True)
        dict_ids = {}
        for number, voice in enumerate(voices_new):
            if number == 5:
                break
            dict_ids.update({voice["user_id"]: [voice["voice_count"], voice["voice_duration"]]})
        users_vk = self.kristy.vk.users.get(user_ids=list(dict_ids.keys()))
        response += " \nТоп 5 по общей длительности: \n"
        for number, user in enumerate(users_vk):
            response += str(number + 1) + ". {0} {1} (⌛".format(user['first_name'], user['last_name'])
            if dict_ids[user['id']][1] // 86400 > 0:
                response += ' ' + str(dict_ids[user['id']][1] // 86400) + ' дн.'
            if dict_ids[user['id']][1] % 86400 // 3600 > 0:
                response += ' ' + str(dict_ids[user['id']][1] % 86400 // 3600) + ' ч.'
            if dict_ids[user['id']][1] % 3600 // 60 > 0:
                response += ' ' + str(dict_ids[user['id']][1] % 3600 // 60) + ' м.'
            if dict_ids[user['id']][1] % 60 > 0:
                response += ' ' + str(dict_ids[user['id']][1] % 60) + ' с.'
            response += ') \n'
        self.kristy.send(peer, response)
