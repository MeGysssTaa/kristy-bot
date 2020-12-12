import ranks
import keyboards
from vkcommands import VKCommand


class ChooseChat(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='почта_тег_выбор',
                           desc='Показывает все теги почты в беседе',
                           usage='???',
                           dm=True)

    def execute(self, chat, peer, sender, args=None, attachments=None):
        page_list = args["page_list"]
        tags_from_db = self.kristy.db.all_email_tags(chat)
        tags_from_db.sort()
        tags = [{"name": tag,
                 "argument": tag,
                 "color": ""} for tag in tags_from_db]
        if not tags_from_db:
            self.kristy.send(peer, "Нету тегов почты", [], keyboards.start_keyboard(chat))
        else:
            response, keyboard = keyboards.choose_keyboard(chat=chat,
                                                           response="Выберите тег",
                                                           buttons=tags,
                                                           page_list=page_list,
                                                           action_now="почта_тег_выбор",
                                                           action_to='почта_событие_выбор',
                                                           action_from='стартовая_клавиатура')
            self.kristy.send(peer, response, None, keyboard)
