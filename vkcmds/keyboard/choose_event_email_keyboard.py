import ranks
import keyboards
from vkcommands import VKCommand
from datetime import *

class ChooseChat(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='почта_событие_выбор',
                           desc='Показывает все события в текущей почте',
                           usage='???',
                           dm=True)

    def execute(self, chat, peer, sender, args=None, attachments=None, fwd_messages=None):
        page_list = args["page_list"]
        tag = args["parameters"][-1]
        future_events = self.kristy.db.get_future_events_email(chat, tag)
        events_sorted = sorted(self.kristy.db.get_events_for_email(chat, tag), key=lambda x: x["date"], reverse=True)
        events = [{"name": datetime.strftime(event["date"], "%d.%m.%Y %H:%M") , "argument": event["id"], "color": "green" if event in future_events else ""} for event in events_sorted]
        if not events:
            self.kristy.send(peer, "Нету событий")
        else:
            response, keyboard = keyboards.choose_keyboard(chat=chat,
                                                           response="Выберите событие",
                                                           buttons=events,
                                                           page_list=page_list,
                                                           action_now="почта_событие_выбор",
                                                           action_to='почта_событие',
                                                           action_from='почта_тег_выбор',
                                                           parameters=args["parameters"])
            self.kristy.send(peer, response, None, keyboard)