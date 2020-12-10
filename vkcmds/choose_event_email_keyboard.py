import ranks
import keyboards
from vkcommands import VKCommand


class ChooseChat(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='почта_событие_выбор',
                           desc='Показывает все теги почты в беседе',
                           usage='???',
                           dm=True)

    def execute(self, chat, peer, sender, args=None, attachments=None):
        page_list = args["page_list"] if "page_list" in args else [0]
        tag = args["argument"]
        events_sorted = sorted(self.kristy.db.get_events_for_email(chat, tag), key=lambda x: x['id'], reverse=True)
        events = [{"name": event["date"], "argument": event["id"], "color": ""} for event in events_sorted]
        if not events:
            self.kristy.send(peer, "Нету событий")
        else:
            response, keyboard = keyboards.choose_keyboard(chat, "Выберите событие", events, page_list + [0], "почта_событие", 'почта_событие_выбор', 'почта_тег_выбор', tag)
            self.kristy.send(peer, response, None, keyboard)