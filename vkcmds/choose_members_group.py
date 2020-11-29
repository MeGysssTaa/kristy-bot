import ranks
import keyboards
from vkcommands import VKCommand


class ChooseChat(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='состав_группы_выбор',
                           desc='Выбор группы для отображения участников группы',
                           usage='???',
                           dm=True)

    def execute(self, chat, peer, sender, args=None, attachments=None):
        page_list = args["page_list"] if "page_list" in args else [0]
        existing = self.kristy.db.get_all_groups(chat)
        groups = []
        for group in existing:
            groups.append([group + ' (' + str(len(self.kristy.db.get_members_group(chat, group))) + ')', group])
        if not existing:
            self.kristy.send(peer, "Групп не найдено", [], keyboards.start_keyboard(chat))
        else:
            response, keyboard = keyboards.choose_keyboard(chat, "Выберите группу", groups, page_list, "состав_группы", 'состав_группы_выбор', 'стартовая_клавиатура')
            self.kristy.send(peer, response, None, keyboard)

