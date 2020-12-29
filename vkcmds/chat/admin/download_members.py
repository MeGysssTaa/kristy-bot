import ranks
import keyboards
from vkcommands import VKCommand


class ChooseChat(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='загрузить',
                           desc='Загружает всех пользователей в беседе в бд',
                           usage='!загрузить',
                           min_rank=ranks.Rank.ADMIN)

    def execute(self, chat, peer, sender, args=None, attachments=None, fwd_messages=None):
        try:
            chat_info = self.kristy.vk.messages.getConversationMembers(peer_id=peer)
            for member in chat_info['items']:
                if not self.kristy.db.get_user_rank(chat, member['member_id']):
                    self.kristy.db.add_user_to_chat(chat, member['member_id'])
            self.kristy.send(peer, 'Успешно обновила базу данных пользователей')
        except:
            self.kristy.send(peer, 'У меня нет админки((. Дайте пожалуйста 😢')
