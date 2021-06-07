import json
import os
from fuzzywuzzy import fuzz
import ranks
import keyboards
from vkcommands import VKCommand


class ChooseChat(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='рандом',
                           desc='Показывает рандомное голосовое, которое было в чате')

    def execute(self, chat, peer, sender, args: str = None, attachments=None, fwd_messages=None):
        audio_users_ids = self.kristy.db.get_all_random_voices(chat)
        if len(audio_users_ids) == 0:
            self.kristy.send(peer, "У вас нет ещё голосовых сообщений")
            return
        if len(args) == 0:
            audios = []
            for audios_user in audio_users_ids.values():
                audios += audios_user
            voice = audios[int(os.urandom(2).hex(), 16) % len(audios)]
        else:
            user_name = ' '.join(args)
            name_surname = surname = name = []
            users_vk = self.kristy.vk.users.get(user_ids=list(audio_users_ids.keys()))
            for user_vk in users_vk:
                if fuzz.ratio(user_name, "{} {}".format(user_vk['first_name'], user_vk['last_name'])) >= 90 \
                        or fuzz.ratio(user_name, "{} {}".format(user_vk['last_name'], user_vk['first_name'])) >= 90:
                    name_surname.append(user_vk["id"])
                if fuzz.ratio(user_name, user_vk['last_name']) >= 90:
                    surname.append(user_vk["id"])
                if fuzz.ratio(user_name, user_vk['first_name']) >= 90:
                    name.append(user_vk["id"])
            if len(name_surname) > 0:
                audios_user = audio_users_ids[str(name_surname[os.urandom(1)[0] % len(name_surname)])]
            elif len(surname) > 0:
                audios_user = audio_users_ids[str(surname[os.urandom(1)[0] % len(surname)])]
            elif len(name) > 0:
                audios_user = audio_users_ids[str(name[os.urandom(1)[0] % len(name)])]
            else:
                self.kristy.send(peer, "Не найдено совпадений!")
                return
            voice = audios_user[int(os.urandom(2).hex(), 16) % len(audios_user)]
        self.kristy.send(peer, "", voice)
