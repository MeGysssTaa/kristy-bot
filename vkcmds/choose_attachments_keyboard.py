import keyboards
from vkcommands import VKCommand


class ChooseChat(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='вложение_выбор',
                           desc='Выбор вложения, чтобы показать',
                           usage='???',
                           dm=True)

    def execute(self, chat, peer, sender, args=None, attachments=None):
        # TODO покрасить в зелённый цвет свои вложения
        page_list = args["page_list"]
        tags_list = self.kristy.db.get_tag_attachments(chat)
        tags_list.sort()
        tags = [{"name": tag, "argument": tag, "color": ""} for tag in tags_list]
        if not tags:
            self.kristy.send(peer, "Нет вложений в беседе", [], keyboards.information_keyboard(chat))
        else:
            response, keyboard = keyboards.choose_keyboard(chat=chat,
                                                           response="Выберите вложение",
                                                           buttons=tags,
                                                           page_list=page_list,
                                                           action_now="вложение_выбор",
                                                           action_to='вложение',
                                                           action_from='информация')
            self.kristy.send(peer, response, None, keyboard)