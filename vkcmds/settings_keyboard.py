import ranks
import keyboards
from vkcommands import VKCommand


class ChooseChat(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='настройки',
                           desc='Показывает участников выбранной группы',
                           usage='???',
                           dm=True)

    def execute(self, chat, peer, sender, args=None, attachments=None):
        setting = args['argument'] if ('argument' in args and args['argument']) else ""
        target_cmd = None
        for command in self.kristy.vkcmdmgr.commands:
            if command.dm and command.label == setting:
                target_cmd = command
                break
        if target_cmd is not None:
            target_cmd.execute(chat, peer, sender, args, None)
        else:
            self.kristy.send(peer, 'Команда не найденна', [], keyboards.start_keyboard(chat))