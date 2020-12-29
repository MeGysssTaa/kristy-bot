import ranks
from vkcommands import VKCommand


# TODO !!! задержка на команду (на все команды) !!!
# TODO !!! задержка на команду (на все команды) !!!
# TODO !!! задержка на команду (на все команды) !!!
class TimetableCommand(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='расписание',
                           desc='Позволяет управлять расписанием (новая ссылка, вывод текущей, перезагрузка файла)',
                           usage='!расписание [ссылка на новый файл | "обновить"]',
                           min_rank=ranks.Rank.ADMIN)

    def execute(self, chat, peer, sender, args=None, attachments=None, fwd_messages=None):
        if args:
            new_url = args[0]

            if new_url.lower() == 'обновить':
                # Перезагружаем расписание по текущей ссылке.
                self.kristy.send(peer, '⌛ Перезагружаю расписание беседы')
                self.kristy.tt_data.load_timetable(chat)
            else:
                # Устанавливаем новую ссылку.
                if new_url.startswith('http://') or new_url.startswith('https://'):
                    # Всё выглядит ОК. Попытаемся сразу же и перезагрузить расписание.
                    self.kristy.db.set_timetable_url(chat, new_url)
                    self.kristy.send(peer, '✔ Успешно обновила ссылку на файл с расписанием беседы')
                    self.kristy.send(peer, '⌛ Перезагружаю расписание беседы')
                    self.kristy.tt_data.load_timetable(chat)
                else:
                    self.kristy.send(peer, '⚠ Неподдерживаемый тип ссылки. '
                                           'В начале обязательно должно быть "http://" или "https://". \n\n'
                                           '💡 Для обновления (перезагрузки) расписания используйте '
                                           '"!расписание обновить".')
        else:
            # Выводим текущую ссылку.
            cur_url = self.kristy.db.get_timetable_url(chat)

            if cur_url:
                self.kristy.send(peer, '🌐 Текущий файл с расписанием: ' + cur_url)
            else:
                self.kristy.send(peer, '❌ Файл с расписанием для этой беседы не указан. '
                                       'Используйте "!расписание ССЫЛКА_НА_ФАЙЛ", чтобы исправить это.')
