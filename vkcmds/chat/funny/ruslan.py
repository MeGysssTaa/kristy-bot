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
                   "Пока не ясно, попробуй снова", "Спроси позже", "Лучше не рассказывать", "Сейчас нельзя предсказать", "Сконцентрируйся и спроси опять",
                   "Даже не думай", "Мой ответ — «нет»", "По моим данным — «нет»", "Перспективы не очень хорошие", "Весьма сомнительно"]
        final_answer = answers[os.urandom(1)[0] % 20]
        self.kristy.send(peer, final_answer)