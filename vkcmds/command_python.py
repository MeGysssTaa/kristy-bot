import ranks
import keyboards
from vkcommands import VKCommand


class ChooseChat(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='команда',
                           desc='Показывает описание команды',
                           usage='???',
                           dm=True)

    def execute(self, chat, peer, sender, args=None, attachments=None):
        command_label = args['argument'] if ('argument' in args and args['argument']) else ""
        sender_rank = self.kristy.db.get_user_rank_val(chat, sender)
        for command in self.kristy.vkcmdmgr.commands:
            if not command.dm and sender_rank >= command.min_rank.value and command.label == command_label:
                response = 'Описание: \n{0} \nИспользование: \n{1} \n'.format(command.desc, command.usage)
                self.kristy.send(peer, response)
                return

        self.kristy.send(peer, "Ой", keyboards.start_keyboard(chat))