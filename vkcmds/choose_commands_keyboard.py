import ranks
import keyboards
from vkcommands import VKCommand


class ChooseChat(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='команда_выбор',
                           desc='Выбор команды для помощи',
                           usage='???',
                           dm=True)

    def execute(self, chat, peer, sender, args=None, attachments=None):
        page_list = args["page_list"]
        sender_rank = self.kristy.db.get_user_rank_val(chat, sender)
        commands_sorted = sorted(self.kristy.vkcmdmgr.commands, key=lambda command: (-command.min_rank.value, command.label))
        commands = [{"name": command.label, "argument": command.label, "color": ""} for command in commands_sorted if not command.dm and sender_rank >= command.min_rank.value]
        if not commands:
            self.kristy.send(peer, "У вас нет прав, кек", [], keyboards.information_keyboard(chat))
        else:
            response, keyboard = keyboards.choose_keyboard(chat=chat,
                                                           response="Выберите команду",
                                                           buttons=commands,
                                                           page_list=page_list,
                                                           action_now="команда_выбор",
                                                           action_to='команда',
                                                           action_from='информация')
            self.kristy.send(peer, response, None, keyboard)
