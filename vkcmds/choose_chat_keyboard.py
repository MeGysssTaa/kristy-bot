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

    def execute(self, chat, peer, sender, args=None, attachments=None):
        page_list = args["page_list"] if "page_list" in args else [0]
        chats_sender = self.kristy.db.get_user_chats(sender)
        chats = [{'name': chat_now['name'], "argument": chat_now['chat_id'], "color": "green" if chat == chat_now['chat_id'] else ""} for chat_now in chats_sender]
        if not chats_sender:
            self.kristy.send(peer, "Вас нет ни в одной беседе")
        else:
            response, keyboard = keyboards.choose_keyboard(chat, "Выберите беседу", chats, page_list, "стартовая_клавиатура", 'выбор_беседы', 'настройки' if chat != -1 else None)
            self.kristy.send(peer, response, None, keyboard)
