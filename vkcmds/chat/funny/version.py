from vkcommands import VKCommand


class Version(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='версия',
                           desc='Отображает информацию о запущенной в данный момент версии бота.')

    def execute(self, chat, peer, sender, args=None, attachments=None, fwd_messages=None):
        self.kristy.send(peer, '🔃 Текущая версия бота: ' + self.kristy.version)
