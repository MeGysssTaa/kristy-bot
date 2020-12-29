import ranks
from vkcommands import VKCommand
import keyboards
import antony_modules


class DeleteGroup(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='удалить_вложение',
                           desc='Удалить вложение.',
                           usage='???',
                           dm=True,
                           min_rank=ranks.Rank.MODERATOR)

    def execute(self, chat, peer, sender, args=None, attachments=None, fwd_messages=None):
        page_list = args['page_list']
        parameters = args['parameters'] if 'parameters' in args else []
        if len(parameters) == 0:
            self.choose_attachment(chat, peer, page_list)
        elif len(parameters) == 1:
            self.confirm(chat, peer, page_list, parameters)
        elif len(parameters) == 2:
            self.delete_attachment(chat, peer, page_list, parameters)

    def delete_attachment(self, chat, peer, page_list, parameters):
        tag, status = parameters
        if status:
            self.kristy.db.remove_attachment(chat, tag)
            response = "Успешно удалила вложение"
            self.choose_attachment(chat, peer, page_list, response)
        else:
            response = "Отменила удаление вложения"
            self.choose_attachment(chat, peer, page_list, response)

    def confirm(self, chat, peer, page_list, parameters):
        tag = parameters[-1]
        attachment = self.kristy.db.get_attachment(chat, tag)
        if not attachment:
            response = "Не найдено вложение"
            self.choose_attachment(chat, peer, page_list, response)
        else:
            self.kristy.send(peer, attachment["message"], attachment["attachments"])
            keyboard = keyboards.confirm_keyboard(chat=chat,
                                                  action='удалить_вложение',
                                                  parameters=parameters,
                                                  page_list=page_list)
            response = 'Вы действительно хотите удалить это вложение: {0}?'.format(tag)
            self.kristy.send(peer, response, None, keyboard)

    def choose_attachment(self, chat, peer, page_list, response=""):
        tags_list = self.kristy.db.get_tag_attachments(chat)
        tags_list.sort()
        tags = [{"name": tag, "argument": tag, "color": ""} for tag in tags_list]
        if not tags:
            self.kristy.send(peer, "Нет вложений в беседе" if not response else response, [], keyboards.delete_keyboard(chat))
        else:
            response_keyboard, keyboard = keyboards.choose_keyboard(chat=chat,
                                                                    response="Выберите вложение",
                                                                    buttons=tags,
                                                                    page_list=page_list,
                                                                    action_now="удалить_вложение",
                                                                    action_to='удалить_вложение',
                                                                    action_from='удалить')
            self.kristy.send(peer, response_keyboard if not response else response, None, keyboard)
