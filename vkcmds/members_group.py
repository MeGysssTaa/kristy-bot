import ranks
import keyboards
from vkcommands import VKCommand


class ChooseChat(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='участники_группы',
                           desc='Показывает участников выбранной группы',
                           usage='???',
                           dm=True)

    def execute(self, chat, peer, sender, args=None, attachments=None):
        group = args['argument'] if ('argument' in args and args['argument']) else ""
        existing = self.kristy.db.get_all_groups(chat)
        if group not in existing:
            self.kristy.send(peer, 'Такой группы нет', [], keyboards.information_keyboard(chat))

        members = self.kristy.db.get_group_members(chat, group)
        if members:
            response = 'Участники: \n'
            users_vk = self.kristy.vk.users.get(user_ids=members)
            users = sorted(users_vk, key=lambda user: (user["first_name"], user["last_name"]))
            for number, user in enumerate(users):
                response += str(number + 1) + ". " + user["first_name"] + " " + user[
                    "last_name"] + " \n"
            self.kristy.send(peer, response)
        else:
            self.kristy.send(peer, 'Эта группа пуста', [], keyboards.information_keyboard(chat))