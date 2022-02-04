import traceback

import kss
import ranks
from vkcommands import VKCommand


class KSSCommand(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='сценарий',
                           desc='Создаёт сценарий KSS из переданной строки и выполняет его.',
                           min_args=1,
                           usage='!сценарий <текст сценария>',
                           min_rank=ranks.Rank.ADMIN)

    def execute(self, chat, peer, sender, args=None, attachments=None, fwd_messages=None):
        try:
            script = kss.parse(' '.join(args), self.kristy.tt_data.script_globals[chat])
        except SyntaxError as e:
            self.kristy.send(2E9 + chat, '⚠ Не удалось создать сценарий: ' + str(e))
            traceback.print_exc()
            return

        # noinspection PyBroadException
        try:
            script.execute(self.kristy, chat, self.kristy.kss_executor.get_variables(chat))
        except Exception:
            self.kristy.send(2E9 + chat, '⚠ Ошибка выполнения сценария: см. консоль')
            traceback.print_exc()
