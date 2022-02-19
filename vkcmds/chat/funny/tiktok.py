import random
import re

from vkcommands import VKCommand


class ChooseChat(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='ткиток',
                           desc='Показывает видос из тиктока')

    def execute(self, chat, peer, sender, args: str = None, attachments=None, fwd_messages=None):
        pass
