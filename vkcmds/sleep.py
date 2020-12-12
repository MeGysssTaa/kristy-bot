import antony_modules
import time
import datetime
from vkcommands import VKCommand


class ChooseChat(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='спать',
                           desc='Не знаю зачем нужна',
                           usage='!спать')

    def execute(self, chat, peer, sender, args=None, attachments=None):
        self.kristy.send(peer, "На ремонте")
        return
        time_do = (86400 - (time.mktime((datetime.datetime.utcnow() + datetime.timedelta(hours=2)).timetuple())) % 86400) % 3600 // 60
        time_dict = {
            ("6:00", "8:00"): "уже утро нахрен",
            ("8:00", "22:00"): "еще не скоро",
            ("22:00", "23:00"): "уже скоро",
            ("23:00", "00:00"): "через {0} {1}".format(str(time_do),
                                                       "минута" if time_do % 10 == 1 and time_do != 11 else "минуты" if 2 <= time_do % 10 <= 4 and not 12 <= time_do <= 14 else "минут"),
            ("00:00", "1:00"): "можно ложиться",
            ("1:00", "2:00"): "ложись дурачёк",
            ("2:00", "3:00"): "УЖЕ 2 ЧАСА НОЧИ",
            ("3:00", "4:00"): "вставать через 5 часов...",
            ("4:00", "5:00"): "understandable",
            ("5:00", "6:00"): "zzz"
        }
        self.kristy.send(peer, antony_modules.time_intervals(time_dict, "Ошибка"))
