import ranks
from vkcommands import VKCommand


class Test(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='бд',
                           desc='Меняет название беседы в базе данных бота.',
                           usage='!название <новое_название>',
                           min_rank=ranks.Rank.ADMIN)

    def execute(self, chat, peer, sender, args=None, attachments=None, fwd_messages=None):
        for a in self.kristy.db.all_chat_ids():
            self.kristy.send(peer, f"chat: {a} \n {self.kristy.db.get_users(a)}")
