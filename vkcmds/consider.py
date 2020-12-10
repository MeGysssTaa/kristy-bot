import ranks
import keyboards
from vkcommands import VKCommand


class ChooseChat(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='посчитать',
                           desc='Подсчитывает выражение',
                           usage='!посчитать <выражение>',
                           min_rank=ranks.Rank.PRO,
                           min_args=1)

    def execute(self, chat, peer, sender, args=None, attachments=None):
        expression = ' '.join(args)
        self.kristy.send(peer, str(eval(expression)))