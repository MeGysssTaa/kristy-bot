import timetable
from vkcommands import VKCommand


class NextClass(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='пара',
                           desc='Отображает информацию о следующей паре. Эта информация может зависеть ' +
                                'от того, в каких группах находится использовавший эту команду.')

    def execute(self, chat, peer, sender, args=None, attachments=None):
        sender_groups = self.kristy.db.get_user_groups(chat, sender)
        next_class = timetable.next_class(self.kristy.tt_data, chat, sender_groups)

        if next_class is None:
            self.kristy.send(peer, '🛌 На сегодня всё. Иди поспи, что ли.')
        else:
            time_left = timetable.time_left(self.kristy.tt_data, chat, next_class.start_tstr)
            time_left_str = 'До начала ' + time_left + '.' if time_left is not None else 'Занятие вот-вот начнётся!'
            self.kristy.send(peer, '📚 Следующая пара: %s. %s' % (next_class, time_left_str))
