import timetable
from vkcommands import VKCommand


class ClassesToday(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='пары',
                           usage='!пары [группа1] [группа2] [...] [группаN]',
                           desc='Отображает информацию о сегодняшних парах. Эта информация может зависеть ' +
                                'от того, в каких группах находится использовавший эту команду.')

    def execute(self, chat, peer, sender, args=None, attachments=None, fwd_messages=None):
        target_groups = args if args else self.kristy.db.get_user_groups(chat, sender)
        today_weekday = timetable.weekday_ru(self.kristy.tt_data, chat)
        classes_today = timetable.get_all_classes(self.kristy.tt_data, chat, today_weekday, target_groups)
        name_data = self.kristy.vk.users.get(user_id=sender)[0]
        response = '%s' % (name_data['first_name'])

        if len(classes_today) == 0:
            self.kristy.send(peer, '🛌 %s, сегодня пар нет. Баиньки.' % response)
        else:
            result = '📚 %s, расписание на сегодня:\n\n' % response

            for class_data in classes_today:
                result += ' • %s—%s — %s (%s)\n\n' % (class_data.start_tstr,
                                                      class_data.end_tstr,
                                                      class_data.name,
                                                      class_data.host)

            result += '\n💡 Информация актуальна для участников групп'

            if len(target_groups) == 1:
                result += 'ы'

            result += ' \"%s\"' % target_groups[0]

            for i in range(1, len(target_groups)):
                result += ', \"%s\"' % target_groups[i]

            result += '.'

            self.kristy.send(peer, result)
