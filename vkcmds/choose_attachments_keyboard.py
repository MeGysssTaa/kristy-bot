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
        page_list = args["page_list"] if "page_list" in args else [0]
        tags_list = self.kristy.db.get_tag_attachments(chat)
        tags_list.sort()
        tags = [{"name": tag, "argument": tag, "color": ""} for tag in tags_list]
        if not tags:
            self.kristy.send(peer, "Нет вложений в беседе", [], keyboards.information_keyboard(chat))
        else:
            response, keyboard = keyboards.choose_keyboard(chat, "Выберите вложение", tags, page_list, "вложение", 'вложение_выбор', 'информация')
            self.kristy.send(peer, response, None, keyboard)