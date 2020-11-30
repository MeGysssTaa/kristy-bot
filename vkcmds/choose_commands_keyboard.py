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
        page_list = args["page_list"] if "page_list" in args else [0]
        sender_rank = self.kristy.db.get_user_rank_val(chat, sender)
        commands = []
        for command in self.kristy.vkcmdmgr.commands:
            if not command.dm and sender_rank >= command.min_rank.value:
                commands.append([command.label + ' ({0})'.format(command.min_rank.name), command.label])

        if not commands:
            self.kristy.send(peer, "У вас нет прав, кек", [], keyboards.start_keyboard(chat))
        else:
            response, keyboard = keyboards.choose_keyboard(chat, "Выберите команду", commands, page_list, "команда", 'команда_выбор', 'стартовая_клавиатура')
            self.kristy.send(peer, response, None, keyboard)
