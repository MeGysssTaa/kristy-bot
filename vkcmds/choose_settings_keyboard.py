import ranks
import keyboards
from vkcommands import VKCommand


class ChooseChat(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='настройки_выбор',
                           desc='Выбор настроек',
                           usage='???',
                           dm=True)


    def execute(self, chat, peer, sender, args=None, attachments=None):
        page_list = args["page_list"] if "page_list" in args else [0]
        settings = [
            ["Выбор беседы", "выбор_беседы"]
        ]
        if not settings:
            self.kristy.send(peer, "Настройки не найдены", [], keyboards.start_keyboard(chat))
        else:
            response, keyboard = keyboards.choose_keyboard(chat, "Выберите настройки", settings, page_list, "настройки", 'настройки_выбор', 'стартовая_клавиатура')
            self.kristy.send(peer, response, None, keyboard)