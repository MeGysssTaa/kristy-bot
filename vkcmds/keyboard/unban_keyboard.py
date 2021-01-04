import keyboards
from vkcommands import VKCommand
import time


class ChooseChat(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='разбан',
                           desc='Показывает время до разбана',
                           usage='???',
                           dm=True)

    def execute(self, chat, peer, sender, args=None, attachments=None, fwd_messages=None):
        if sender not in self.kristy.killed[chat]:
            self.kristy.send(peer, "У вас не было бана")
        else:
            if self.kristy.killed[chat][sender] + self.kristy.TIMEBAN * 60 * 60 < time.time():
                self.kristy.send(peer, "Бан прошёл")
            else:
                response = '⌛ Осталось: '
                if int(self.kristy.killed[chat][sender] + self.kristy.TIMEBAN * 60 * 60 - time.time()) // 3600 > 0:
                    response += ' ' + str(int(self.kristy.killed[chat][sender] + self.kristy.TIMEBAN * 60 * 60 - time.time()) // 3600) + ' ч.'
                if int(self.kristy.killed[chat][sender] + self.kristy.TIMEBAN * 60 * 60 - time.time()) % 3600 // 60 > 0:
                    response += ' ' + str(int(self.kristy.killed[chat][sender] + self.kristy.TIMEBAN * 60 * 60 - time.time()) % 3600 // 60) + ' м.'
                if int(self.kristy.killed[chat][sender] + self.kristy.TIMEBAN * 60 * 60 - time.time()) % 60 > 0:
                    response += ' ' + str(int(self.kristy.killed[chat][sender] + self.kristy.TIMEBAN * 60 * 60 - time.time()) % 60) + ' с.'
                self.kristy.send(peer, response)
