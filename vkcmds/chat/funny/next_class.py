from typing import List

import timetable
from vkcommands import VKCommand


class NextClass(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='пара',
                           usage='!пара [группа1] [группа2] [...] [группаN]',
                           desc='Отображает информацию о следующей паре. Эта информация может зависеть ' +
                                'от того, в каких группах находится использовавший эту команду.')

    def execute(self, chat, peer, sender, args=None, attachments=None, fwd_messages=None):
        target_groups = args if args else self.kristy.db.get_user_groups(chat, sender)
        NextClass.respond(self.kristy, chat, peer, sender, target_groups)

    @staticmethod
    def respond(kristy, chat: int, peer: int, sender: int, target_groups: List[str]):
        next_class = timetable.next_class(kristy.tt_data, chat, target_groups)
        name_data = kristy.vk.users.get(user_id=sender)[0]
        response = '%s' % (name_data['first_name'])

        if next_class is None:
            kristy.send(peer, '🛌 %s, на сегодня всё. Баиньки.' % response)
        else:
            time_left = timetable.time_left(kristy.tt_data, chat, next_class.start_tstr)
            time_left_str = 'До начала ' + time_left + '.' \
                if time_left is not None \
                else 'Занятие вот-вот начнётся!'

            to_whom = '\n\n💡 Информация актуальна для участников групп'

            if len(target_groups) == 1:
                to_whom += 'ы'

            to_whom += ' \"%s\"' % target_groups[0]

            for i in range(1, len(target_groups)):
                to_whom += ', \"%s\"' % target_groups[i]

            to_whom += '.'

            kristy.send(peer, '📚 %s, следующая пара: %s. %s %s'
                        % (response, next_class, time_left_str, to_whom))
