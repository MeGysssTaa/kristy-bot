from vkcommands import VKCommand


class Wiki(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='wiki',
                           desc='Выводит ссылку на Wiki (справку) бота.')

    def execute(self, chat, peer, sender, args=None, attachments=None, fwd_messages=None):
        self.kristy.send(peer, '👉 https://github.com/MeGysssTaa/kristy-bot/wiki')
