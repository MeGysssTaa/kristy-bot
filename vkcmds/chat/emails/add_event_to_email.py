import time
from datetime import *
import ranks
from vkcommands import VKCommand


class AddEventToEmail(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='событие+',
                           desc='Добавляет событие к существующей почте по тегу.',
                           usage='!событие+ <тег> <дата (ДД.ММ)|(ДД.ММ.ГГГГ)> <время (ЧЧ:ММ)> [текст] // Чтобы добавить вложения, прикрепите их к сообщению с командой (максимум 4)',
                           min_args=3,
                           min_rank=ranks.Rank.USER)

    def execute(self, chat, peer, sender, args=None, attachments=None, fwd_messages=None):
        format_date_full = "%d.%m.%Y"
        format_date = "%d.%m"
        format_time = "%H:%M"
        zone = timedelta(hours=2)
        tag = args[0].lower()
        all_tags = self.kristy.db.all_email_tags(chat)
        if tag not in all_tags:
            self.kristy.send(peer, "Данная почта не создана")
            return

        date_str = args[1]
        time_str = args[2]
        message = ' '.join(args[3:]) if len(args) > 3 else ''
        try:
            date_to_db = datetime.strptime(date_str + ' ' + time_str, '{0} {1}'.format(format_date_full, format_time))
        except ValueError:
            try:
                date_time_now = datetime.utcnow() + zone
                date_to_db = datetime.strptime(date_str + ' ' + time_str, '{0} {1}'.format(format_date, format_time)).replace(year=date_time_now.year)
                if date_to_db < date_time_now:
                    date_to_db.replace(year=date_time_now.year + 1)
            except ValueError:
                self.kristy.send(peer, "Неверный формат даты или времени")
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
