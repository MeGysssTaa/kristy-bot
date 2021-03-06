import keyboards
from vkcommands import VKCommand


class ChooseChat(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='отключиться_выбор',
                           desc='Выбор групп, в которых вы есть',
                           usage='???',
                           dm=True)

    def execute(self, chat, peer, sender, args=None, attachments=None, fwd_messages=None):
        page_list = args["page_list"]
        object_groups = self.kristy.db.get_object_all_groups(chat)
        sender_groups = self.kristy.db.get_user_groups(chat, sender)
        groups_sorted = sorted([{"name": group["name"], "count": len(group["members"])} for group in object_groups if group["name"] in sender_groups],
                               key=lambda group: (-group["count"], group["name"]))
        groups = [{"name": "{0} ({1})".format(group["name"], str(group["count"])),
                   "argument": group["name"],
                   "color": ""} for group in groups_sorted]
        if not groups:
            self.kristy.send(peer, "Вас нет в группах", [], keyboards.control_keyboard(chat))
        else:
            response, keyboard = keyboards.choose_keyboard(chat=chat,
                                                           response="Выберите группу",
                                                           buttons=groups,
                                                           page_list=page_list,
                                                           action_now="отключиться_выбор",
                                                           action_to='отключиться',
                                                           action_from='управление')
            self.kristy.send(peer, response, None, keyboard)