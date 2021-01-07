import re

import ranks
import vkcommands
from vkcommands import VKCommand


class RemoveMembersFromGroups(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='отключить',
                           desc='Отключает указанных людей от указанных групп.',
                           usage='!отключить <@юзер1> [@юзер2] [...] [@юзерN] > <группа1> [группа2] [...] [группаM]',
                           min_args=3,
                           min_rank=ranks.Rank.MODERATOR)

    def execute(self, chat, peer, sender, args=None, attachments=None, fwd_messages=None):
        if '>' not in args or args.count('>') > 1:
            self.print_usage(peer)
            return
        users = re.findall(r'\[id(\d+)\|[^]]+\]', ' '.join(list(set(args[:args.index('>')]))))
        groups = re.findall(r'[a-zA-Zа-яА-ЯёЁ0-9_]+', ' '.join(args[args.index('>') + 1:] if len(args) - 1 > args.index('>') else []))
        if not users or not groups:
            self.print_usage(peer)
            return

        users = [int(user) for user in users]
        existing_groups = self.kristy.db.get_all_groups(chat)
        existing_users = self.kristy.db.get_users(chat)

        not_found = []
        left = {}
        for user in users:
            if user in existing_users:
                left.update({user: []})
                sender_groups = self.kristy.db.get_user_groups(chat, user)
                for group in groups:
                    if group in existing_groups and group in sender_groups:
                        self.kristy.db.leave_group(chat, group, user)
                        left[user].append(group)
                if not left[user]:
                    del left[user]
            else:
                not_found.append(user)

        all_users_vk = self.kristy.vk.users.get(user_ids=users)
        first_names_left = ""
        first_names_not_found = ""
        for user_vk in all_users_vk:  # хрен его знает, мб потом переделаем
            if user_vk["id"] in left:
                first_names_left += "{0} > {1} \n".format("{0} {1}".format(user_vk["first_name"], user_vk["last_name"]),
                                                          ' '.join(left[user_vk["id"]]))
            if user_vk["id"] in not_found:
                first_names_not_found += "{0} {1} \n".format(user_vk["first_name"], user_vk["last_name"])

        if peer > 2E9:
            name_data = self.kristy.vk.users.get(user_id=sender)[0]
            sender_name = name_data['first_name'] + ' ' + name_data['last_name']
            response = sender_name + '\n'
        else:
            response = ''

        if first_names_left:
            response += 'Отключила: \n'
            response += first_names_left

        if first_names_not_found:
            response += 'Данных пользователей нет в базе данных: \n'
            response += first_names_not_found

        if not first_names_not_found and not first_names_left:
            response += 'Никого не отключила'

        self.kristy.send(peer, response)