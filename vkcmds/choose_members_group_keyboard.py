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
        page_list = args["page_list"]
        object_groups = self.kristy.db.get_object_all_groups(chat)
        groups_sorted = sorted([{"name": group["name"], "count": len(group["members"])} for group in object_groups],
                               key=lambda group: (-group["count"], group["name"]))
        sender_groups = self.kristy.db.get_user_groups(chat, sender)
        groups = [{"name": "{0} ({1})".format(group["name"], str(group["count"])),
                   "argument": group["name"],
                   "color": "green" if group["name"] in sender_groups else ""} for group in groups_sorted]
        if not groups:
            self.kristy.send(peer, "Групп не найдено", [], keyboards.information_keyboard(chat))
        else:
            response, keyboard = keyboards.choose_keyboard(chat=chat,
                                                           response="Выберите группу",
                                                           buttons=groups,
                                                           page_list=page_list,
                                                           action_now='участники_группы_выбор',
                                                           action_to="участники_группы",
                                                           action_from='информация')
            self.kristy.send(peer, response, None, keyboard)

