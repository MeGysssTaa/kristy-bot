import ranks
import re
from vkcommands import VKCommand
import os
import threading


class Ruslan(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='разбан',
                           desc='Даёт разбан людей',
                           usage='!разбан <@ участников>',
                           min_args=1,
                           min_rank=ranks.Rank.MODERATOR)

    def execute(self, chat, peer, sender, args=None, attachments=None, fwd_messages=None):
        users = set(re.findall(r'\[id(\d+)\|[^]]+\]', ' '.join(args)))
        users = [int(user) for user in users]
        if not users:
            self.print_usage(peer)
            return
        unbanned = []
        existing_users = self.kristy.db.get_users(chat)
        for user in users:
            if user in existing_users and user in self.kristy.killed[chat]:
                unbanned.append(user)
                self.kristy.killed[chat].pop(user)

        if not unbanned:
            self.kristy.send(peer, "Никто не в бане, либо их нет в беседе")
            return
        all_users_vk = self.kristy.vk.users.get(user_ids=users)
        response = "Сняла бан:\n"
        for user_vk in all_users_vk:
            smile = list(bytes('😀', 'utf-8'))[:-1] + [bytes('😀', 'utf-8')[-1] + os.urandom(1)[0] % (int(bytes('👿', 'utf-8')[-1] - bytes('😀', 'utf-8')[-1]))]
            response += '{0} {1} \n'.format(str(bytearray(smile), 'utf-8'), user_vk['first_name'] + ' ' + user_vk['last_name'])
        self.kristy.send(peer, response)
