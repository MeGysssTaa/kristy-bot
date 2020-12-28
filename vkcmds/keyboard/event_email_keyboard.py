import ranks
import keyboards
from vkcommands import VKCommand


class ChooseChat(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='почта_событие',
                           desc='Показывает выбранное событие',
                           usage='???',
                           dm=True)

    def execute(self, chat, peer, sender, args=None, attachments=None):
        tag, event_id = args["parameters"]
        event = self.kristy.db.get_event_email(chat, tag, event_id)
        if not event:
            self.kristy.send(peer, "Не найдено событие")
        else:
            self.kristy.send(peer, event["message"], event["attachments"])