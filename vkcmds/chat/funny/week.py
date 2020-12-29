import time

import ranks
import vkcommands
from vkcommands import VKCommand


class Week(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='неделя',
                           desc='Отображает информацию о чётности текущей недели.')

    def execute(self, chat, peer, sender, args=None, attachments=None, fwd_messages=None):
        if int(time.strftime("%W", time.gmtime(time.time() + 2 * 60 * 60))) % 2:
            week = 'нижняя'
        else:
            week = 'верхняя'
        emoji = '☝' if week == 'верхняя' else '👇'
        self.kristy.send(peer, str("Сейчас %s %s %s неделя" % (emoji, week, emoji)).upper())