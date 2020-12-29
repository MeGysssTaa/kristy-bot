import ranks
from vkcommands import VKCommand
import keyboards
import antony_modules
from datetime import *


class DeleteGroup(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='удалить_почту',
                           desc='Удалить почту.',
                           usage='???',
                           dm=True,
                           min_rank=ranks.Rank.MODERATOR)

    def execute(self, chat, peer, sender, args=None, attachments=None, fwd_messages=None):
        page_list = args['page_list']
        parameters = args['parameters'] if 'parameters' in args else []
        if len(parameters) == 0:
            self.choose_email(chat, peer, page_list)
        elif len(parameters) == 1:
            self.confirm(chat, peer, page_list, parameters)
        elif len(parameters) == 2:
            self.delete_email(chat, peer, page_list, parameters)

    def delete_email(self, chat, peer, page_list, parameters):
        tag, status = parameters
        if status:
            self.kristy.db.delete_email(chat, tag)
            response = "Успешно удалила почту"
            self.choose_email(chat, peer, page_list, response)
        else:
            response = "Отменила удаление почты"
            self.choose_email(chat, peer, page_list, response)

    def confirm(self, chat, peer, page_list, parameters):
        tag = parameters[-1]
        all_tags = self.kristy.db.all_email_tags(chat)
        if tag not in all_tags:
            response = "Не найдена почта"
            self.choose_email(chat, peer, page_list, response)
        else:
            events = self.kristy.db.get_events_for_email(chat, tag)

            if events:
                keyboard = keyboards.confirm_keyboard(chat=chat,
                                                      action='удалить_почту',
                                                      parameters=parameters,
                                                      page_list=page_list)
                count_active = len(self.kristy.db.get_future_events_email(chat, tag))
                response = 'Вы действительно хотите удалить эту почту: {0}? \n' \
                           'В ней {1} {2} {3}{4}.'.format(tag,
                                                          "находятся" if len(events) > 1 else "находится",
                                                          str(len(events)),
                                                          antony_modules.correct_shape(["событие", "события", "событий"],
                                                                                       len(events)),
                                                          " ({0} {1})".format(count_active,
                                                                              antony_modules.correct_shape(["активное", "активных", "активных"],
                                                                                                           count_active)))
                self.kristy.send(peer, response, None, keyboard)
            else:
                self.delete_email(chat, peer, page_list, [tag, True])

    def choose_email(self, chat, peer, page_list, response=""):
        tags_from_db = self.kristy.db.all_email_tags(chat)
        tags_from_db.sort()
        tags = [{"name": "{0} ({1})".format(tag, str(len(self.kristy.db.get_events_for_email(chat, tag)))),
                 "argument": tag,
                 "color": ""} for tag in tags_from_db]
        if not tags:
            self.kristy.send(peer, "Нету тегов почты" if not response else response, [], keyboards.delete_keyboard(chat))
        else:
            response_keyboard, keyboard = keyboards.choose_keyboard(chat=chat,
                                                                    response="Выбетите тег почты",
                                                                    buttons=tags,
                                                                    page_list=page_list,
                                                                    action_now="удалить_почту",
                                                                    action_to='удалить_почту',
                                                                    action_from='удалить')
            self.kristy.send(peer, response_keyboard if not response else response, None, keyboard)
