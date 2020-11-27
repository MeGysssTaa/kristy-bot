import traceback

import ranks


ALL_MENTIONS = ['all', 'все', 'online', 'онлайн', 'здесь', 'here', 'тут', 'everyone']


class VKCommandsManager:
    def __init__(self, kristy):
        from vkcmds import (
            add_group,
            next_class
        )

        self.kristy = kristy
        self.commands = (
            add_group.AddGroup(kristy),
            next_class.NextClass(kristy)
        )

    def handle_chat_cmd(self, event):
        """
        Обработка команд в беседе.
        """
        chat = event.chat_id
        peer = event.object.message['peer_id']
        sender = event.object.message['from_id']
        msg = event.object.message['text'].strip()
        attachments = event.object.message['attachments']

        if sender not in self.kristy.db.get_users(chat):
            self.kristy.db.add_user_to_chat(chat, sender)

        if len(msg) > 1 and msg.startswith('!'):
            # Команды
            spl = msg[1:].split(' ')
            label = spl[0].lower()
            args = spl[1:] if len(spl) > 1 else []
            target_cmd = None

            for command in self.commands:
                if not command.dm and command.label == label:
                    target_cmd = command
                    break

            if target_cmd is not None:
                # TODO (совсем потом) выполнять команды через пул потоков
                target_cmd.process(chat, peer, sender, args, attachments)
        # TODO:
        # elif len(msg) > 1 and msg.startswith('?'):
        #     # Вложения
        #     tag = msg[1:].split(' ')[0].lower()
        #     vk_cmds.exec_use_attachment(chat, peer, label)
        # if re.findall(r"(?:\s|^)@([a-zA-Zа-яА-ЯёЁ0-9_]+)(?=[\s .,:;?()!]|$)", msg):
        #     vk_cmds.exec_ping_groups(chat, peer, sender,
        #                              re.findall(r"(?:\s|^)@([a-zA-Zа-яА-ЯёЁ0-9_]+)(?=[\s .,:;?()!]|$)", msg))
        # if re.findall(r"(?:\s|^)@([a-zA-Zа-яА-ЯёЁ0-9_]+)\+(?=[\s .,:;?()!]|$)", msg):
        #     vk_cmds.exec_sending_messages(chat, peer, sender,
        #                                   re.findall(r"(?:\s|^)@([a-zA-Zа-яА-ЯёЁ0-9_]+)\+(?=[\s .,:;?()!]|$)", msg),
        #                                   msg, attachments)
        # if forbidden_names.findall(msg):
        #     vk_cmds.exec_impostor_track(chat, sender)

    def handle_user_kb_cmd(self, event):
        pass

    def handle_user_text_cmd(self, event):
        pass


class VKCommand:
    def __init__(self, kristy, label, desc,
                 min_rank=ranks.Rank.WORKER, usage=None, min_args=0, dm=False, process_attachments=False):
        self.kristy = kristy
        self.label = label
        self.usage = usage
        self.desc = desc
        self.min_args = min_args
        self.dm = dm
        self.min_rank = min_rank
        self.process_attachments = process_attachments

    def print_usage(self, peer):
        if self.usage is not None:
            self.kristy.send(peer, '⚠ Использование: \n' + self.usage)

    def print_no_perm(self, peer):
        self.kristy.send(peer, '⛔ Нет прав ⛔')

    def process(self, chat, peer, sender, args, attachments=False):
        # noinspection PyBroadException
        try:
            if chat != -1 and self.kristy.db.get_user_rank_val(chat, sender) < self.min_rank.value:
                self.print_no_perm(peer)
            elif len(args) < self.min_args:
                self.print_usage(peer)
            else:
                self.execute(chat, peer, sender, args, attachments)
        except Exception:
            self.kristy.send(peer, 'Ты чево наделол......\n\n' + traceback.format_exc())
            traceback.print_exc()

    def execute(self, chat, peer, sender, args=None, attachments=None):
        pass  # наследуется
