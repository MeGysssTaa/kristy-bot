import os

import requests

from vkcommands import VKCommand


class ChooseChat(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='gif',
                           desc='Выдаёт рандомную гифку',
                           usage='!gif <тег>')

    def execute(self, chat, peer, sender, args: str = None, attachments=None, fwd_messages=None):
        msg = ' '.join(args) if args else ''
        url = f"https://api.giphy.com/v1/gifs/random?api_key=rEJQmgKYm3vewdvY2NQF0GRY2bN1FARj&tag={msg}&rating=g"
        s = requests.Session()
        while True:
            response = s.get(url=url).json()
            if response["data"]:
                break
        gif_url = response.json()["data"]["images"]["original"]["url"]
        doc_data = requests.get(gif_url).content
        with open('../tmp/doc{0}.gif'.format(chat), 'wb') as handler:
            handler.write(doc_data)
        upload = self.kristy.vk_upload.document_message(doc=f'../tmp/doc{chat}.gif', peer_id=peer, title=f'doc{chat}')
        os.remove(f'../tmp/doc{chat}.gif')
        quote_doc = 'doc{0}_{1}'.format(upload['doc']["owner_id"], upload['doc']["id"])
        self.kristy.send(peer, "", quote_doc)