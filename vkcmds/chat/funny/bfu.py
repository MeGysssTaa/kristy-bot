from vkcommands import VKCommand


class ChooseMembers(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='бфу',
                           desc='Показывает всю красоту БФУ (локальные мемы в массы).',
                           usage='!бфу')

    def execute(self, chat, peer, sender, args=None, attachments=None, fwd_messages=None):
        self.kristy.send(peer, "", ["photo-199300529_457239023"])
