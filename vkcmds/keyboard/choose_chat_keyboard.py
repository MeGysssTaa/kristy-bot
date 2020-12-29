import ranks
import keyboards
from vkcommands import VKCommand


class ChooseChat(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='выбор_беседы',
                           desc='Выбор активной беседы',
                           usage='???',
                           dm=True,
                           min_rank=ranks.Rank.GOVNO)

    def execute(self, chat, peer, sender, args=None, attachments=None, fwd_messages=None):
        page_list = args["page_list"]
        chats_sender = self.kristy.db.get_user_chats(sender)
        chats = [{'name': chat_now['name'], "argument": chat_now['chat_id'], "color": "green" if chat == chat_now['chat_id'] else ""} for chat_now in chats_sender]
        if not chats_sender:
            self.kristy.send(peer, "Вас нет ни в одной беседе")
        else:
            response, keyboard = keyboards.choose_keyboard(chat=chat,
                                                           response="Выберите беседу",
                                                           buttons=chats,
                                                           page_list=page_list,
                                                           action_now="выбор_беседы",
                                                           action_to='стартовая_клавиатура',
                                                           action_from='настройки' if chat != -1 else None)
            self.kristy.send(peer, response, None, keyboard)
