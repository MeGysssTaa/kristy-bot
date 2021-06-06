import json
from pprint import pprint
import time
import requests

import ranks
import keyboards
from vkcommands import VKCommand
import threading


class ChooseChat(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='загрузить',
                           desc='Загруэает голосовые файлы (временная)',
                           usage='!загрузить <голосовой файл>',
                           min_rank=ranks.Rank.ADMIN)

    def execute(self, chat, peer, sender, args=None, attachments=None, fwd_messages=None):
        print(attachments)
        if not attachments or attachments[0]["type"] != "doc":
            self.kristy.send(peer, "Нет документа")
            return
        threading.Thread(target=self.downloadThread, args=(chat, peer, attachments[0]["doc"],)).start()

    def downloadThread(self, chat, peer, doc):
        doc_file = requests.get(doc["url"]).content
        with open('../tmp/{}{}.txt'.format(str(doc["title"]).rsplit('.')[0], chat), 'wb') as handler:
            handler.write(doc_file)

        with open('../tmp/{}{}.txt'.format(str(doc["title"]).rsplit('.')[0], chat), 'r') as file:
            audios_list = json.load(file)
            self.kristy.db.delete_all_voices(chat)
            for voice_id in audios_list:
                self.kristy.db.add_new_random_voice(chat, voice_id)
        self.kristy.send(peer, "Успешно обновлены голосовые ({})".format(len(audios_list)))

