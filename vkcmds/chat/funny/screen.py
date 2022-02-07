import random
import re

from vkcommands import VKCommand


class ChooseChat(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='скрин',
                           desc='Показывает скрин из аниме')

    def execute(self, chat, peer, sender, args: str = None, attachments=None, fwd_messages=None):
        albums = self.kristy.vk_user.photos.getAlbums(owner_id=-21102748)
        album = random.SystemRandom().choice(albums["items"])
        while not re.match(r".+[|\\/].+", album["title"]):
            album = random.SystemRandom().choice(albums["items"])
        self.kristy.anime[chat] = album["title"]
        random_number = random.SystemRandom().randint(0, album["size"] - 1)
        photo = "photo-199300529_457239560"
        for i in range(3):
            photos = self.kristy.vk_user.photos.get(owner_id=-21102748, album_id=album["id"], count=1, photo_sizes=1, offset=random_number)
            photo = photos["items"][0]
            image_url = photo["sizes"][-1]["url"]
            try:
                photo = self.kristy.get_list_attachments([{"type": "photo", "photo": {"sizes": [{"width": 400, "url": image_url}]}}], peer)[0]
                break
            except Exception:
                pass
        self.kristy.send(peer, "", attachment=photo)
