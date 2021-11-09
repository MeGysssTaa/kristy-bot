import os

import requests

import antony_modules
import time
import datetime

import ranks
from vkcommands import VKCommand


class ChooseChat(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='звук',
                           desc='Создаёт звук к картинке',
                           usage='!звук <вложение>',
                           min_rank=ranks.Rank.PRO,
                           min_args=1)

    def execute(self, chat, peer, sender, args=None, attachments=None, fwd_messages=None):
        if not attachments or attachments[0]["type"] != 'photo':
            self.kristy.send(peer, "Нету фотографии")
        max_photo_url = ""
        max_width = 0
        for photo in attachments[0]['photo']['sizes']:
            if max_width < photo['width']:
                max_width = photo['width']
                max_photo_url = photo['url']

        data = {"link": max_photo_url}
        r = requests.post("https://backend.imaginarysoundscape.net/process?save=1", data=data)
        url_sound = f"https://imaginary-soundscape.s3-ap-northeast-1.amazonaws.com/sounds/{r.json()['sound_id']}.mp3"
        mp3_data = requests.get(url_sound).content
        time_now = time.time()
        with open('../tmp/audio{0}.mp3'.format(time_now), 'wb') as audio:
            audio.write(mp3_data)
        upload = self.kristy.vk_upload.audio_message(audio='../tmp/audio{0}.mp3'.format(time_now), peer_id=peer)
        os.remove('../tmp/audio{0}.mp3'.format(time_now))
        self.kristy.send(peer, "", 'audio_message{0}_{1}'.format(upload['audio_message']["owner_id"], upload['audio_message']["id"]))
