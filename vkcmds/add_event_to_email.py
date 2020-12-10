import time
import ranks
from vkcommands import VKCommand


class AddEventToEmail(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='событие',
                           desc='Добавляет событие к существующей почте по тегу.',
                           usage='!событие <тег> <дата ДД.ММ> or <дата_время ДД.ММ:ЧЧ.ММ> [текст] // Чтобы добавить вложения, прикрепите их к сообщению с командой (максимум 4)',
                           min_args=2,
                           min_rank=ranks.Rank.USER)

    def execute(self, chat, peer, sender, args=None, attachments=None):
        format_date_time = "%d.%m:%H.%M"
        format_date = "%d.%m"
        format_date_string = "ДД.ММ"
        timezone = 2 * 60 * 60  # +2 часа
        tag = args[0].lower()

        all_tags = self.kristy.db.all_email_tags(chat)
        if tag not in all_tags:
            self.kristy.send(peer, "Данная почта не создана")
            return

        date_string = args[1]
        message = args[2:] if len(args) > 2 else []
        message = ' '.join(message)

        try:
            date_event = time.strptime(date_string, format_date_time)
            time_now_struct = time.gmtime(time.time() + timezone)
            if date_event.tm_mon > time_now_struct.tm_mon or (date_event.tm_mon == time_now_struct.tm_mon and date_event.tm_mday > time_now_struct.tm_mday
            ) or (date_event.tm_mon == time_now_struct.tm_mon and date_event.tm_mday == time_now_struct.tm_mday and date_event.tm_hour > time_now_struct.tm_hour
            ) or (date_event.tm_mon == time_now_struct.tm_mon and date_event.tm_mday == time_now_struct.tm_mday and date_event.tm_hour == time_now_struct.tm_hour and date_event.tm_min >= time_now_struct.tm_min):
                date_to_db = '.'.join([str(date_event.tm_mday).rjust(2, '0'), str(date_event.tm_mon).rjust(2, '0'), str(time_now_struct.tm_year)]) + ' ' + ':'.join([str(date_event.tm_hour).rjust(2, '0'), str(date_event.tm_min).rjust(2, '0')])
            else:
                date_to_db = '.'.join([str(date_event.tm_mday).rjust(2, '0'), str(date_event.tm_mon).rjust(2, '0'), str(time_now_struct.tm_year + 1)]) + ' ' + ':'.join([str(date_event.tm_hour).rjust(2, '0'), str(date_event.tm_min).rjust(2, '0')])
        except ValueError:
            try:
                date_event = time.strptime(date_string, format_date)
                time_now_struct = time.gmtime(time.time() + timezone)
                if date_event.tm_mon > time_now_struct.tm_mon or (date_event.tm_mon == time_now_struct.tm_mon and date_event.tm_mday >= time_now_struct.tm_mday):
                    date_to_db = '.'.join([str(date_event.tm_mday).rjust(2, '0'), str(date_event.tm_mon).rjust(2, '0'), str(time_now_struct.tm_year)]) + ' ' + ':'.join([str(time_now_struct.tm_hour).rjust(2, '0'), str(time_now_struct.tm_min).rjust(2, '0')])
                else:
                    date_to_db = '.'.join([str(date_event.tm_mday).rjust(2, '0'), str(date_event.tm_mon).rjust(2, '0'), str(time_now_struct.tm_year + 1)]) + ' ' + ':'.join([str(time_now_struct.tm_hour).rjust(2, '0'), str(time_now_struct.tm_min).rjust(2, '0')])
            except ValueError:
                self.kristy.send(peer, "Неверный формат даты. Формат: " + format_date_string)
                return
        if not message and not attachments:
            self.print_usage(peer)
            return

        list_attachments = self.kristy.get_list_attachments(attachments, peer)

        if not list_attachments and not message:
            self.kristy.send(peer, "Не удалось создать")
            return

        event_id = self.kristy.db.create_event(chat, tag, date_to_db, message, list_attachments)

        self.kristy.send(peer, "Успешно добавлено новое событие " + str(event_id))
        pass
