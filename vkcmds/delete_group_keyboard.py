import ranks
from vkcommands import VKCommand
import keyboards
import antony_modules


class DeleteGroup(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='удалить_группу',
                           desc='Удалить группу.',
                           usage='???',
                           dm=True)

    def execute(self, chat, peer, sender, args=None, attachments=None):
        page_list = args['page_list']
        parameters = args['parameters'] if 'parameters' in args else []
        if len(parameters) == 0:
            self.choose_group(chat, peer, sender, page_list)
        elif len(parameters) == 1:
            self.confirm(chat, peer, sender, page_list, parameters)
        elif len(parameters) == 2:
            self.delete_group(chat, peer, sender, page_list, parameters)

    def delete_group(self, chat, peer, sender, page_list, parameters):
        group, status = parameters
        sender_created_groups = self.kristy.db.get_user_created_groups(chat, sender)
        rank_sender_value = self.kristy.db.get_user_rank_val(chat, sender)
        if status:
            if group not in sender_created_groups and rank_sender_value < ranks.Rank.MODERATOR.value:
                response = "Нет прав на удаление этой группы"
                self.choose_group(chat, peer, sender, page_list, response)
            else:
                self.kristy.db.delete_group(chat, group)
                response = "Успешно удалила группу"
                self.choose_group(chat, peer, sender, page_list, response)
        else:
            response = "Отменила удаление группы"
            self.choose_group(chat, peer, sender, page_list, response)

    def confirm(self, chat, peer, sender, page_list, parameters):
        group = parameters[-1]
        existing = self.kristy.db.get_all_groups(chat)
        sender_created_groups = self.kristy.db.get_user_created_groups(chat, sender)
        if group not in existing:
            response = "Не найдена группа"
            self.choose_group(chat, peer, sender, page_list, response)
        elif group not in sender_created_groups and self.kristy.db.get_user_rank_val(chat, sender) < ranks.Rank.MODERATOR.value:
            response = "Нет доступа к этой группе"
            self.choose_group(chat, peer, sender, page_list, response)
        else:
            members_group = self.kristy.db.get_group_members(chat, group)

            if len(members_group) > 1 or (len(members_group) == 1 and sender not in members_group):
                keyboard = keyboards.confirm_keyboard(chat=chat,
                                                      action='удалить_группу',
                                                      parameters=parameters,
                                                      page_list=page_list)
                response = 'Вы действительно хотите удалить эту группу: {0}? \n' \
                           'В ней {1} {2} {3}{4}.'.format(group,
                                                          "состоят" if len(members_group) - int(sender in members_group) > 1 else "состоит",
                                                          str(len(members_group) - int(sender in members_group)),
                                                          antony_modules.correct_shape(["участник", "участника", "участников"],
                                                                                       len(members_group) - int(sender in members_group)),
                                                          " помимо вас" if sender in members_group else "")
                self.kristy.send(peer, response, None, keyboard)
            else:
                self.delete_group(chat, peer, sender, page_list, [group, True])

    def choose_group(self, chat, peer, sender, page_list, response=""):
        object_groups = self.kristy.db.get_object_all_groups(chat)
        sender_groups = self.kristy.db.get_user_groups(chat, sender)
        rank_sender_value = self.kristy.db.get_user_rank_val(chat, sender)
        groups_sorted = sorted([{"name": group["name"], "count": len(group["members"])} for group in object_groups if sender == group["creator"] or rank_sender_value >= ranks.Rank.MODERATOR.value],
                               key=lambda group: (-group["count"], group["name"]))
        groups = [{"name": "{0} ({1})".format(group["name"], str(group["count"])),
                   "argument": group["name"],
                   "color": "green" if group["name"] in sender_groups else ""} for group in groups_sorted]
        if not groups:
            self.kristy.send(peer, "Нету групп, которые вы можете удалить" if not response else response, [], keyboards.delete_keyboard(chat))
        else:
            response_keyboard, keyboard = keyboards.choose_keyboard(chat=chat,
                                                                    response="Выбетите группу",
                                                                    buttons=groups,
                                                                    page_list=page_list,
                                                                    action_now="удалить_группу",
                                                                    action_to='удалить_группу',
                                                                    action_from='удалить')
            self.kristy.send(peer, response_keyboard if not response else response, None, keyboard)
