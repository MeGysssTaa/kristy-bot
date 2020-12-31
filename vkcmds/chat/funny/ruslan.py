import ranks
import os
from vkcommands import VKCommand


class Ruslan(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='руслан',
                           desc='Руслан, просто Руслан.',
                           usage='!руслан',
                           min_rank=ranks.Rank.PRO)

    def execute(self, chat, peer, sender, args=None, attachments=None, fwd_messages=None):
        answers = ["Бесспорно", "Предрешено", "Никаких сомнений", "Определённо да", "Можешь быть уверен в этом",
                   "Мне кажется - «да»", "Вероятнее всего", "Хорошие перспективы", "Знаки говорят - «да»", "Да",
                   "Даже не думай", "Мой ответ — «нет»", "По моим данным — «нет»", "Перспективы не очень хорошие", "Весьма сомнительно",
                   "Сомнительно", "Хочеться в это верить", "Даже Бабенко в такое не поверит", "Ты думал я скажу да?", "Даже я не могу предсказать ответ"]
        final_answer = answers[os.urandom(1)[0] % len(answers)]
        self.kristy.send(peer, final_answer)