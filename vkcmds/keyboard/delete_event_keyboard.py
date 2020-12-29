import ranks
from vkcommands import VKCommand
import keyboards
from datetime import *

class DeleteEmails(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='удалить_событие',
                           desc='Удаляет событие',
                           usage='???',
                           min_rank=ranks.Rank.MODERATOR,
                           dm=True)

    def execute(self, chat, peer, sender, args=None, attachments=None, fwd_messages=None):
        page_list = args['page_list']
        parameters = args['parameters'] if 'parameters' in args else []
        if len(parameters) == 0:
            self.choose_email(chat, peer, page_list)
        elif len(parameters) == 1:
            self.choose_event(chat, peer, page_list, parameters)
        elif len(parameters) == 2:
            self.confirm(chat, peer, page_list, parameters)
        elif len(parameters) == 3:
            self.delete_event(chat, peer, page_list, parameters)

    def delete_event(self, chat, peer, page_list, parameters):
        tag, event_id, status = parameters
        if status:
            self.kristy.db.delete_event(chat, tag, event_id)
            response = "Успешно удалила событие"
            self.choose_event(chat, peer, page_list, [tag], response)
        else:
            response = "Отменила удаление события"
            self.choose_event(chat, peer, page_list, [tag], response)

    def confirm(self, chat, peer, page_list, parameters):
        tag, event_id = parameters
        event = self.kristy.db.get_event_email(chat, tag, event_id)
        if not event:
            response = "Не найдено событие"
            self.choose_event(chat, peer, page_list, [tag], response)
        else:
            self.kristy.send(peer, event["message"], event["attachments"])
            keyboard = keyboards.confirm_keyboard(chat=chat,
                                                  action='удалить_событие',
                                                  parameters=parameters,
                                                  page_list=page_list)
            response = 'Вы действительно хотите удалить это событие?'
            self.kristy.send(peer, response, None, keyboard)

    def choose_event(self, chat, peer, page_list, parameters, response=""):
        tag = parameters[-1]
        events_sorted = sorted(self.kristy.db.get_events_for_email(chat, tag), key=lambda x: x['date'], reverse=True)
        events = [{"name": datetime.strftime(event["date"], "%d.%m.%Y %H:%M"), "argument": event["id"], "color": ""} for event in events_sorted]
        if not events:
            if not response:
                response = "Нету событий \n\n"
            self.choose_email(chat, peer, page_list[:-1], response)
        else:
            response_keyboard, keyboard = keyboards.choose_keyboard(chat=chat,
                                                                    response="Выберите событие",
                                                                    buttons=events,
                                                                    page_list=page_list,
                                                                    action_now="удалить_событие",
                                                                    action_to='удалить_событие',
                                                                    action_from='удалить_событие',
                                                                    parameters=parameters)
            self.kristy.send(peer, response_keyboard if not response else response, None, keyboard)

    def choose_email(self, chat, peer, page_list, response=""):
        tags_from_db = self.kristy.db.all_email_tags(chat)
        tags_from_db.sort()
        tags = []
        for tag in tags_from_db:
            count = len(self.kristy.db.get_events_for_email(chat, tag))
            if count:
                tags.append({"name": "{0} ({1})".format(tag, str(count)),
                             "argument": tag,
                             "color": ""})
        if not tags:
            self.kristy.send(peer, "Нету тегов почты, в которых есть события" if not response else response, [], keyboards.delete_keyboard(chat))
        else:
            response_keyboard, keyboard = keyboards.choose_keyboard(chat=chat,
                                                                    response="Выбетите тег почты",
                                                                    buttons=tags,
                                                                    page_list=page_list,
                                                                    action_now="удалить_событие",
                                                                    action_to='удалить_событие',
                                                                    action_from='удалить')
            self.kristy.send(peer, response_keyboard if not response else response, None, keyboard)
