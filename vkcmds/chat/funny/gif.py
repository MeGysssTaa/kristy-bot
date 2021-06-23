import os

import requests
from bs4 import BeautifulSoup

from vkcommands import VKCommand


class ChooseChat(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='гифка',
                           desc='Показывает гифку')

    def execute(self, chat, peer, sender, args: str = None, attachments=None, fwd_messages=None):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.106 Safari/537.36'}
        page_soup = BeautifulSoup(requests.get("http://xdgif.ru/random/", headers=headers).text, 'html.parser')
        items = page_soup.find_all('div', class_='entry')
        gif_url = items[0].find('img').get('src')
        doc_data = requests.get(gif_url).content
        with open('../tmp/doc{0}.gif'.format(chat), 'wb') as handler:  # TODO возможность одинаковых файлов, починить в будущем
            handler.write(doc_data)
        upload = self.kristy.vk_upload.document_message(doc=f'../tmp/doc{chat}.gif', peer_id=peer, title=f'doc{chat}')
        os.remove(f'../tmp/doc{chat}.gif')
        quote_doc = 'doc{0}_{1}'.format(upload['doc']["owner_id"], upload['doc']["id"])
        self.kristy.send(peer, "", quote_doc)