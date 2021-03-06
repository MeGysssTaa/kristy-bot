import re

import ranks
from vkcommands import VKCommand


class JoinMembersToGroup(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='группа>',
                           desc='Подключает указанных людей к указанным группам.',
                           usage='!группа> <@юзер1> [@юзер2] [...] [@юзерN] > <группа1> [группа2] [...] [группаM]',
                           min_args=3,
                           min_rank=ranks.Rank.MODERATOR)

    def execute(self, chat, peer, sender, args=None, attachments=None, fwd_messages=None):
        if '>' not in args or args.count('>') > 1:
            self.print_usage(peer)
            return
        users = re.findall(r'(?=^|\s)\[id(\d+)\|[^]]+\]+(?=\s|$)', ' '.join(args[:args.index('>')]))
        groups = re.findall(r'(?:^|\s)[a-zA-Zа-яА-ЯёЁ0-9_]+(?:\s|$)', ' '.join(args[args.index('>') + 1:] if len(args) - 1 > args.index('>') else []))
        if not users or not groups:
            self.print_usage(peer)
            return

        users = [int(user) for user in users]
        existing_groups = self.kristy.db.get_all_groups(chat)
        existing_users = self.kristy.db.get_users(chat)

        not_found = []
        joined = {}
        for user in users:
            if user in existing_users:
                joined.update({user: []})
                sender_groups = self.kristy.db.get_user_groups(chat, user)
                for group in groups:
                    if group in existing_groups and group not in sender_groups:
                        self.kristy.db.join_group(chat, group, user)
                        joined[user].append(group)
                if not joined[user]:
                    del joined[user]
            else:
                not_found.append(user)

        all_users_vk = self.kristy.vk.users.get(user_ids=users)
        first_names_joined = ""
        first_names_not_found = ""
        for user_vk in all_users_vk:  # хрен его знает, мб потом переделаем
            if user_vk["id"] in joined:
                first_names_joined += "{0} > {1} \n".format("{0} {1}".format(user_vk["first_name"], user_vk["last_name"]),
                                                            ' '.join(joined[user_vk["id"]]))
            if user_vk["id"] in not_found:
                first_names_not_found += "{0} {1} \n".format(user_vk["first_name"], user_vk["last_name"])

        if peer > 2E9:
            name_data = self.kristy.vk.users.get(user_id=sender)[0]
            sender_name = name_data['first_name'] + ' ' + name_data['last_name']
            response = sender_name + '\n'
        else:
            response = ''

        if first_names_joined:
            response += 'Добавила: \n'
            response += first_names_joined

        if first_names_not_found:
            response += 'Данных пользователей нет в базе данных: \n'
            response += first_names_not_found

        if not first_names_not_found and not first_names_joined:
            response += 'Никто никуда не добавлен'

        self.kristy.send(peer, response)
