import time

import ranks
import vkcommands
import timetable
from vkcommands import VKCommand


class Week(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='неделя',
                           desc='Отображает информацию о чётности текущей недели.')

    def execute(self, chat, peer, sender, args=None, attachments=None, fwd_messages=None):
        week = timetable.get_week(self.kristy.tt_data, chat)
        
        if week is None:
            self.kristy.send(peer, "⚠ У беседы не настроено расписание. Используется серверное время. Для настройки используйте команду !расписание")
            
            if int(time.strftime("%W", time.gmtime(time.time() + 2 * 60 * 60))) % 2 == 0:
                week = 'нижняя'
            else:
                week = 'верхняя'
        
        emoji = '☝' if week == 'верхняя' else '👇'
        self.kristy.send(peer, str("Сейчас %s %s %s неделя" % (emoji, week, emoji)).upper())
  
