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
        print(args)
        page_list = args["page_list"] if "page_list" in args else [0]
        chats_sender = self.kristy.db.get_chats_user(sender)
        chats = [[chat['name'], chat['chat_id']] for chat in chats_sender]
        if not chats_sender:
            self.kristy.send(peer, "Вас нет ни в одной беседе")
        else:
            response, keyboard = keyboards.choose_keyboard(chat, "Выберите беседу", chats, page_list, "стартовая_клавиатура", 'выбор_беседы')
            self.kristy.send(peer, response, None, keyboard)
