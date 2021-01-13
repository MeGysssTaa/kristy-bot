from vkcommands import VKCommand
import ranks
import time
import requests
from pydub import AudioSegment
import speech_recognition as sr


class Version(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='текст',
                           desc='Переводит голосовое сообщение в текст',
                           min_rank=ranks.Rank.PRO)

    def execute(self, chat, peer, sender, args=None, attachments=None, fwd_messages=None):
        if not fwd_messages:
            self.kristy.send(peer, "Нет голосового сообщения")
            return

        if len(fwd_messages) == 1 and not (fwd_messages[0]['attachments'] and fwd_messages[0]['attachments'][0]['audio_message']):
            self.kristy.send(peer, "Не удалось найти голосовое в пересылаемом сообщении")
            return

        if len(fwd_messages) > 1:
            self.kristy.send(peer, "Пожалуйста, прикрепите только одно сообщение")
            return
        url_mp3 = fwd_messages[0]['attachments'][0]['audio_message']['link_mp3']
        mp3_data = requests.get(url_mp3).content
        time_now = time.time()
        with open('../tmp/audio{0}.mp3'.format(time_now), 'wb') as audio:
            audio.write(mp3_data)

        sound = AudioSegment.from_mp3('../tmp/audio{0}.mp3'.format(time_now))
        sound.export('../tmp/audio{0}.wav'.format(time_now), format="wav")

        r = sr.Recognizer()
        with sr.AudioFile('../tmp/audio{0}.wav'.format(time_now)) as source:
            audio = r.record(source)

        try:
            transcripts = r.recognize_google(audio, language="ru", show_all=True)["alternative"]
            self.kristy.send(peer, transcripts[3]['transcript'] if len(transcripts) > 3 else transcripts[0]['transcript'])
        except Exception:
            self.kristy.send(peer, "Не удалось, либо сообщение пустое")
