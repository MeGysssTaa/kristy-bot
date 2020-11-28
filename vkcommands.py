import glob
import os
import pyclbr
import re
import traceback
from fuzzywuzzy import process

import log_util
import ranks


ALL_MENTIONS = ['all', 'все', 'online', 'онлайн', 'здесь', 'here', 'тут', 'everyone']
ALL_MENTIONS_REGEX = re.compile(
    r"(?:\s|^)" + "(@" + ")|(@".join(ALL_MENTIONS) + ")" + r"(?=[\s .,:;?()!]|$)")
GROUP_PING_REGEX = r"(?:\s|^)@([a-zA-Zа-яА-ЯёЁ0-9_]+)(?=[\s .,:;?()!]|$)"
GROUP_DM_REGEX = r"(?:\s|^)@([a-zA-Zа-яА-ЯёЁ0-9_]+)\+(?=[\s .,:;?()!]|$)"


class VKCommandsManager:
    def __init__(self, kristy):
        self.logger = log_util.init_logging(__name__)
        self.kristy = kristy
        self.commands, self.chat_command_names = self._load_commands()

    def _load_commands(self):
        """
        Рефлективно загружает, инициализирует и регистрирует все команды ВК из модуля 'vkcmds'.

        :return: два списка (list): (1) список экземпляров <? extends VKCommand> загруженных команд,
                                    (2) список названий загруженных команд ДЛЯ БЕСЕД (команды ЛС не включены).
        """
        cmd_submodules = dict()
        abs_search_path = os.path.join(os.path.dirname(__file__), 'vkcmds', '*.py')

        # Ищем все подмодули и все классы в них без импорта самих подмодулей.
        for path in glob.glob(abs_search_path):
            submodule_name = os.path.basename(path)[:-3]  # -3 из-за '.py'
            all_classes = pyclbr.readmodule(f'vkcmds.{submodule_name}')

            # Ищем в подмодуле класс, наследующий VKCommand.
            command_classes = {
                name: info
                for name, info in all_classes.items()
                if 'VKCommand' in info.super
            }

            if command_classes:  # подходящий класс найден
                cmd_submodules[submodule_name] = command_classes

        commands = []  # экземпляры классов зарегистрированных команд
        chat_command_names = []  # названия зарегистрированных команд ДЛЯ БЕСЕД (названия команд для ЛС не включены)

        # Проходимся по подмодулям команд, инициализируем классы команд в них (для каждой
        # команды создаётся один её экземпляр) и добавляем полученные объекты в список команд.
        for submodule_name, cmd_classes in cmd_submodules.items():
            module = __import__(f'vkcmds.{submodule_name}')  # импортируем подмодуль по имени
            submodule = getattr(module, submodule_name)  # получаем сам подмодуль

            # Проходимся по всем классам команд.
            for cmd_class_name in cmd_classes:
                # Создаём экземпляр этого класса (инициализируем его) и добавляем в список команд.
                class_instance = getattr(submodule, cmd_class_name)
                class_instance.__init__(class_instance, 'hi')
                cmd_label = class_instance.label
                dm = class_instance.dm
                commands.append(class_instance)

                if not dm:
                    chat_command_names.append(cmd_label)

                self.logger.info('Загружена команда ВК (%s): "%s"',
                                 'для ЛС' if dm else 'для бесед', cmd_label)

        # Возвращаем список экземпляров загруженных команд и названия этих команд.
        return commands, chat_command_names

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

        # noinspection PyBroadException
        try:
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
                if target_cmd:
                    # TODO (совсем потом) выполнять команды через пул потоков
                    target_cmd.process(chat, peer, sender, args, attachments)
                else:
                    # TODO выделить этот код и дубликат снизу в отдельный метод ("_suggest_cmd")
                    commands_found = process.extract(label, self.chat_command_names)
                    tags_list = self.kristy.db.get_tags(chat)
                    tags_found = process.extract(label, tags_list)

                    response = ""
                    for command in commands_found:
                        if command[1] < 70:
                            break
                        response += '!' + command[0] + ' \n'
                    for tage in tags_found:
                        if tage[1] < 70:
                            break
                        response += '?' + tage[0] + ' \n'
                    if response:
                        self.kristy.send(peer, "Возможно вы имели в виду: \n" + response)
            elif len(msg) > 1 and msg.startswith('?'):
                # Вложения
                tag = msg[1:].split(' ')[0].lower()
                tags_list = self.kristy.db.get_tags(chat)
                if tag in tags_list:
                    self._handle_attachment(chat, tag)
                else:
                    commands_found = process.extract(tag, self.chat_command_names)
                    tags_found = process.extract(tag, tags_list)

                    response = ""
                    for command in commands_found:
                        if command[1] < 70:
                            break
                        response += '!' + command[0] + ' \n'
                    for tage in tags_found:
                        if tage[1] < 70:
                            break
                        response += '?' + tage[0] + ' \n'
                    if response:
                        self.kristy.send(peer, "Возможно вы имели в виду: \n" + response)

            else:
                group_ping = re.findall(GROUP_PING_REGEX, msg)
                group_dm = re.findall(GROUP_DM_REGEX, msg)

                if group_ping:
                    self._handle_group_ping(chat, peer, group_ping, sender)
                if group_dm:
                    self._handle_group_dm(chat, peer, sender, group_dm, msg, attachments)
                if ALL_MENTIONS_REGEX.findall(msg):
                    self.kristy.db.handle_all_abuse(chat, sender)
        except Exception:
            self.kristy.send(peer, 'Ты чево наделол......\n\n' + traceback.format_exc())

    def handle_user_kb_cmd(self, event):
        pass

    def handle_user_text_cmd(self, event):
        pass

    def _handle_attachment(self, chat, tag):
        attachment = self.kristy.db.get_attachment(chat, tag)

        if attachment:
            self.kristy.send(chat + 2E9, attachment["message"], attachment["attachments"])

    def _handle_group_ping(self, chat, peer, groups, sender):
        pings_str = self.kristy.db.pings_str(chat, groups, sender)

        if pings_str:
            user_vk = self.kristy.vk.users.get(user_id=sender)
            self.kristy.send(peer, user_vk[0]['first_name'] + ' ' + user_vk[0]['last_name']
                             + ':\n☝☝☝☝☝☝☝☝☝☝ \n' + pings_str + '\n☝☝☝☝☝☝☝☝☝☝ \n')

    def _handle_group_dm(self, chat, peer, sender, groups, message, attachments):
        sending_list = []

        for group in groups:
            users = self.kristy.db.get_members_group(chat, group)
            for user in users:
                if user not in sending_list:  # добавил, что себе сообщение тоже отправляется
                    sending_list.append(user)
        if sending_list:
            user_vk = self.kristy.vk.users.get(user_id=sender, name_case='ins')
            message = re.sub(GROUP_DM_REGEX, '', message).strip()
            chat_name = self.kristy.db.get_name_chat(chat)
            response = "Отправлено" + " {0} {1} ".format(user_vk[0]["first_name"], user_vk[0][
                "last_name"]) + 'из беседы - ' + chat_name + ': \n' + message
            error_send = []
            list_attachments = self.kristy.get_list_attachments(attachments, peer)
            for user in sending_list:
                # noinspection PyBroadException
                try:
                    self.kristy.send(user, response, list_attachments)
                except Exception:
                    error_send.append(user)

            if error_send:
                response = 'Не удалось отправить этим людям, так как они со мной даже не общались(((: \n'
                users_vk = self.kristy.vk.users.get(user_ids=error_send)
                for number, user_vk in enumerate(users_vk):
                    response += str(number + 1) + '. {0} {1}'.format(user_vk["first_name"],
                                                                     user_vk["last_name"]) + '\n'
                self.kristy.send(peer, response)
            else:
                response = 'Успешно сделала рассылку'
                self.kristy.send(peer, response)


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
