import ranks
import keyboards
from vkcommands import VKCommand


class ChooseChat(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='участники_группы_выбор',
                           desc='Выбор группы для отображения участников группы',
                           usage='???',
                           dm=True)

    def execute(self, chat, peer, sender, args=None, attachments=None):
        page_list = args["page_list"] if "page_list" in args else [0]
        object_groups = self.kristy.db.get_object_all_groups(chat)
        groups_sorted = sorted(sorted([{"name": group["name"], "count": len(group["members"])} for group in object_groups],
                                      key=lambda group: group["name"]),
                               key=lambda group: group["count"],
                               reverse=True)
        groups = [["{0} ({1})".format(group["name"], str(group["count"])), group["name"]] for group in groups_sorted]
        if not groups:
            self.kristy.send(peer, "Групп не найдено", [], keyboards.information_keyboard(chat))
        else:
            response, keyboard = keyboards.choose_keyboard(chat, "Выберите группу", groups, page_list, "участники_группы", 'участники_группы_выбор', 'информация')
            self.kristy.send(peer, response, None, keyboard)

