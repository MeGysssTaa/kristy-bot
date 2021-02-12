import ranks
from vkcommands import VKCommand
import json

class TimetableCommand(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='база',
                           desc='Позволяет управлять расписанием (новая ссылка, вывод текущей, перезагрузка файла)',
                           min_rank=ranks.Rank.ADMIN)

    def execute(self, chat, peer, sender, args=None, attachments=None, fwd_messages=None):
        data = self.kristy.db.get_all()
        self.kristy.send(peer, json.dumps(data))
