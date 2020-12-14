from datetime import *
import time


class Notification:
    """
    Класс уведомлений
    """

    def __init__(self, kristy):
        time_to_event = [1, 4]
        self.kristy = kristy

    def notification_events(self):
        zone = timedelta(hours=2)
        while True:
            date_time = (datetime.utcnow() + zone).replace(second=0, microsecond=0)
            all_chats = self.kristy.db.all_chat_ids()
            for chat in all_chats:
                all_emails = self.kristy.db.all_email_tags(chat)
                if all_emails:
                    response = "Через 4 часа наступят следующие события: \n"
                    number = 1
                    for email in all_emails:
                        events_count = len(self.kristy.db.get_events_with_date(chat, email, date_time, 4))
                        if events_count:
                            response += "{0}. {1} ({2}) \n".format(str(number), email, str(events_count))
                            number += 1
                    if number != 1:
                        self.kristy.send(2E9 + chat, response)
            time.sleep(60 - time.time() % 60)
