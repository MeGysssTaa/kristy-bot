import time
import timetable
from vkcommands import VKCommand


class ChooseMembers(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='ворота',
                           desc='Отображает время до открытия или до закрытия ворот.')

    def execute(self, chat, peer, sender, args=None, attachments=None, fwd_messages=None):
        format_time = '%H:%S'
        timezone = 2 * 60 * 60  # +2 часа
        time_open_gate = [
            ['08:30', '09:00'],
            ['13:00', '14:00'],
            ['17:00', '18:30']
        ]
        time_open_gate.sort()
        time_now_struct = time.gmtime(time.time() + timezone)
        time_now = time_now_struct.tm_hour * 3600 + time_now_struct.tm_min * 60 + time_now_struct.tm_sec

        for number, time_gate in enumerate(time_open_gate):
            # я искал легче путь, но я обожаю время ☻
            time_start_now = time.strptime(time_gate[0], format_time).tm_hour * 60 * 60 + time.strptime(time_gate[0], format_time).tm_min * 60
            time_end_now = time.strptime(time_gate[1], format_time).tm_hour * 60 * 60 + time.strptime(time_gate[1], format_time).tm_min * 60
            time_start_next = time.strptime(time_open_gate[(number + 1) % len(time_open_gate)][0], format_time).tm_hour * 60 * 60 + time.strptime(time_open_gate[(number + 1) % len(time_open_gate)][0], format_time).tm_min * 60
            if time_start_now <= time_now <= time_end_now:
                response = "Ворота открыты. До закрытия "
                time_closing = time_end_now - time_now
                response += timetable.time_left_ru(
                    time_closing // (60 * 60),
                    time_closing % (60 * 60) // 60,
                    time_closing % (60 * 60) % 60
                )
                self.kristy.send(peer, response)
                return
            elif time_end_now < time_now < time_start_next:
                response = "Ворота закрыты. До открытия "
                time_opening = time_start_next - time_now
                response += timetable.time_left_ru(
                    time_opening // (60 * 60),
                    time_opening % (60 * 60) // 60,
                    time_opening % (60 * 60) % 60
                )
                self.kristy.send(peer, response)
                return
            elif (number + 1) == len(time_open_gate) and (time_end_now < time_now or time_now < time_start_next):
                response = "Ворота закрыты. До открытия "
                time_opening = (time_start_next - time_now) if time_start_next > time_now else (24 * 60 * 60 - time_now + time_start_next)
                response += timetable.time_left_ru(
                    time_opening // (60 * 60),
                    time_opening % (60 * 60) // 60,
                    time_opening % (60 * 60) % 60
                )
                self.kristy.send(peer, response)
                return
        self.kristy.send(peer, "Нету времени")
