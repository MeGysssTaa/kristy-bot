import glob
import os
import pyclbr
import re
import threading
import traceback
from typing import Dict, List, Tuple

import requests
from fuzzywuzzy import fuzz
import json
import log_util
import ranks
import keyboards

ALL_MENTIONS = ['all', 'все', 'online', 'онлайн', 'здесь', 'here', 'тут', 'everyone']
ALL_MENTIONS_REGEX = r"(?:\s|^)[@*]({0})(?=[\s.,:;?()!]|$)".format("|".join(ALL_MENTIONS))
GROUP_PING_REGEX = r"(?:\s|^)[@*]([a-zA-Zа-яА-ЯёЁ0-9_]+)(?=[\s .,:;?()!]|$)"
GROUP_DM_REGEX = r"(?:\s|^)[@*]([a-zA-Zа-яА-ЯёЁ0-9_]+)\+(?=[\s .,:;?()!]|$)"


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
        # Ищем все подмодули и все классы в них без импорта самих подмодулей.
        for root, dirs, files in os.walk("vkcmds", topdown=False):
            abs_search_path = os.path.join(os.path.dirname(__file__), root, '*.py')
            for path in glob.glob(abs_search_path):
                submodule_name = os.path.basename(path)[:-3]  # -3 из-за '.py'
                all_classes = pyclbr.readmodule("{0}.{1}".format(root.replace(os.path.sep, '.'), submodule_name))
                # Ищем в подмодуле класс, наследующий VKCommand.
                command_classes = {
                    name: info
                    for name, info in all_classes.items()
                    if 'VKCommand' in info.super
                }
                if command_classes:  # подходящий класс найден
                    cmd_submodules[(root.replace(os.path.sep, '.'), submodule_name)] = command_classes

        commands = []  # экземпляры классов зарегистрированных команд
        chat_command_names = []  # названия зарегистрированных команд ДЛЯ БЕСЕД (названия команд для ЛС не включены)

        # Проходимся по подмодулям команд, инициализируем классы команд в них (для каждой
        # команды создаётся один её экземпляр) и добавляем полученные объекты в список команд.
        for submodule, cmd_classes in cmd_submodules.items():
            submodule_root, submodule_name = submodule
            module = __import__(f'{submodule_root}.{submodule_name}')  # импортируем подмодуль по имени
            for mod in submodule_root.split(".")[1:]:
                module = getattr(module, mod)  # идём до папки
            submodule = getattr(module, submodule_name)  # получаем сам подмодуль
            # Проходимся по всем классам команд.
            for cmd_class_name in cmd_classes:
                # Создаём экземпляр этого класса (инициализируем его) и добавляем в список команд.
                class_instance = getattr(submodule, cmd_class_name)(self.kristy)
                cmd_label = class_instance.label
                dm = class_instance.dm
                commands.append(class_instance)  # короче ты получал класс, а нужно было объект!!!

                if not dm:
                    chat_command_names.append(cmd_label)

                self.logger.info('Загружена команда ВК (%s): "%s"',
                                 'для ЛС' if dm else 'для бесед', cmd_label)

        # Возвращаем список экземпляров загруженных команд и названия этих команд.
        return commands, chat_command_names

    @staticmethod
    def _is_annoying_topic(msg: str) -> bool:
        # noinspection PyBroadException
        try:
            msg_tf: str = VKCommandsManager._utransform("".join(msg.split()).lower())
            print(f'AnnoyingTopicDebug : "{msg}" ---------> "{msg_tf}"')

            annoying: List[str] = [
                'украин',
                'хохол',
                'хох',
                'донецк',
                'луганск',
                'донбас',
                'днр',
                'лнр',
                'путин',
                'доллар',
                'евро',
                'байден',
                'зеленск'
            ]

            for item in annoying:
                if item in msg_tf:
                    print(' ')
                    print(f'ANNOYING')
                    print(f'  Topic: "{item}"')
                    print(f'  Original message: "{msg}"')
                    print(f'  Transformed message: "{msg_tf}')
                    print(' ')

                    return True

            return False
        except Exception:
            traceback.print_exc()
            return False

    @staticmethod
    def _utransform(msg: str) -> str:
        mappings: Dict[str, str] = {
            'у':
                'yuюÝýỲỳŶŷŸÿỸỹẎẏỴỵẙỶỷȲȳɎɏƳƴŬŭɄʉᵾỤụÜüǛǜǗǘǙǚǕǖṲṳÚúÙùÛûṶṷǓȗŰűŬŭƯưủŪūŪ̀ū̀Ū́ūṺṻŪ̃ū̃ŨũṸṹṴṵᶙŲųŲ́ų́Ų̃ų̃ȔȕŮů',
            'к':
                'kƘƙꝀꝁḰḱǨǩḲḳĶķᶄⱩⱪḴḵ',
            'р':
                'qrpṔṕṖṗⱣᵽƤƥᵱᶈŔŕɌɍŘřŖŗṘṙȐȑȒȓṚṛṜṝṞṟꞦꞧⱤɽR̃r̃',
            'а':
                '4a@ÅåǺǻḀḁẚĂăẶặẮắẰằẲẳẴẵȂȃÂâẬậẤấẦầẪẫẨẩẢảǍǎȺⱥȦȧǠǡẠạÄäǞǟÀàȀȁÁáĀāĀ̀ā̀ÃãĄąĄ́ą́Ą̃ą̃A̲a̲ᶏ',
            'и':
                'iйЙ!ỊịĬĭÎîǏǐƗɨÏïḮḯÍíÌìȈȉĮįĮ́Į̃ĪīĪ̀ī̀ᶖỈỉȊȋĨĩḬḭ',
            'н':
                'мmhnĤĥȞȟĦħḨḩⱧⱨẖẖḤḥḢḣḦḧḪḫꞕꜦꜧŃńÑñŇňǸǹṄṅṆṇŅņṈṉṊṋꞤꞥᵰᶇḾḿṀṁṂṃ ̃ ̃ᵯ',
            'о':
                'o0ØøǾǿᶱÖöȪȫÓóÒòÔôỐốỒồỔổỖỗỘộǑǒŐőŎŏȎȏȮȯȰȱỌọƟɵƠơỚớỜờỠỡỢợỞởỎỏŌōṒṓṐṑÕõȬȭṌṍṎṏǪǫȌȍO̩o̩Ó̩ó̩Ò̩ò̩ǬǭO͍o͍',
            'х':
                'xẌẍẊẋX̂x̂ᶍχχΧ',
            'д':
                'dĐđƊɗḊḋḌḍḐḑḒḓĎďḎḏᵭᶁᶑΔδԀ∂ԁ',
            'б':
                'вbьъ8ɃΒβƀḂḃḄḅḆḇƁɓᵬᶀⲂⲃ',
            'с':
                'csĆćĈĉČčĊċḈḉƇƈC̈c̈ȻȼÇçꞔꞒꞓŚśṠṡẛṨṩṤṥṢṣS̩s̩ꞨꞩŜŝṦṧŠšŞşȘșS̈s̈ᶊⱾȿᵴᶳ',
            'г':
                'gǴǵǤǥĜĝǦǧĞğĢģƓɠĠġḠḡꞠꞡᶃΓγҐґЃѓ',
            'л':
                'lĹĺŁłĽľḸḹL̃l̃ĻļĿŀḶḷḺḻḼḽȽƚⱠⱡΛλӅӆԒԓԮԯŁł',
            '':
                '.,:;?#$%^&*()-_=+`~[]{}<>/|\\"'
        }

        for letter, aliases in mappings.items():
            for i, alias in enumerate(aliases):
                msg = msg.replace(alias, letter)

                if i < (len(aliases) - 1):
                    msg = msg.replace(alias + aliases[i+1], letter)

        return msg

    def handle_chat_cmd(self, event):
        """
        Обработка команд в беседе.
        """
        chat = event.chat_id
        peer = event.object.message['peer_id']
        sender = event.object.message['from_id']
        msg = event.object.message['text'].strip()
        attachments = event.object.message['attachments']
        fwd_messages = event.object.message['fwd_messages']
        if sender not in self.kristy.db.get_users(chat) and sender > 0:
            self.kristy.db.add_user_to_chat(chat, sender)

        if attachments and attachments[0]['type'] == 'audio_message':
            self.kristy.db.voice(chat, sender, attachments[0]['audio_message']['duration'])

        if VKCommandsManager._is_annoying_topic(msg):
            # noinspection PyBroadException
            try:
                # !котик
                cat_image = requests.get('https://cataas.com/cat?type=original').content
                with open('../tmp/cat{0}.png'.format(chat), 'wb') as handler:
                    handler.write(cat_image)
                uploads = self.kristy.vk_upload.photo_messages(photos="../tmp/cat{0}.png".format(chat))[0]
                os.remove("../tmp/cat{0}.png".format(chat))
                quote_image = 'photo{0}_{1}'.format(uploads["owner_id"], uploads["id"])
                self.kristy.send(peer, "Может, лучше про котиков?", quote_image)
            except Exception:
                self.kristy.send(peer, "👎🏻")
                traceback.print_exc()

            return

        self.kristy.game_manager.check_minigame(chat, peer, sender, msg)
        # noinspection PyBroadException
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
                target_cmd.process(chat, peer, sender, args, attachments, fwd_messages)
            else:
                self._did_you_mean(chat, peer, label)

        elif len(msg) > 1 and msg.startswith('?'):
            # Вложения
            tag = msg[1:].split(' ')[0].lower()
            tags_list = self.kristy.db.get_tag_attachments(chat)

            if tag in tags_list:
                self._handle_attachment(chat, peer, tag)
            else:
                self._did_you_mean(chat, peer, tag)

        else:
            group_ping = re.findall(GROUP_PING_REGEX, msg.lower())
            group_dm = re.findall(GROUP_DM_REGEX, msg.lower())
            all_ping = re.findall(ALL_MENTIONS_REGEX, msg.lower())

            if group_ping:
                self._handle_group_ping(chat, peer, group_ping, sender)
            if group_dm:
                self._handle_group_dm(chat, peer, sender, group_dm, msg, attachments)
            if all_ping:
                self.kristy.db.handle_all_abuse(chat, sender)

    def handle_user_kb_cmd(self, event):
        """
        Обработка команд в ЛС бота (кнопки).
        """
        payload = json.loads(event.object.message['payload'])
        sender = event.object.message['from_id']
        peer = event.object.message['peer_id']
        if 'action' not in payload or 'chat_id' not in payload:
            print(2)
            return
        chat = payload['chat_id']
        label = payload['action']

        if chat == -1 and label != 'выбор_беседы' and label != 'стартовая_клавиатура':
            self.kristy.send(peer, 'Клавиатура не актуальна, перезапустите её через !клава')
        elif chat != -1 and sender not in self.kristy.db.get_users(chat):
            self.kristy.send(peer, 'Вас нет в беседе (возможно были кикнуты, используйте !клава)')
        else:
            target_cmd = None
            args = payload['args'] if 'args' in payload else {}
            for command in self.commands:
                if command.dm and command.label == label:
                    target_cmd = command
                    break

            if target_cmd is not None:
                # TODO (совсем потом) выполнять команды асинхронно - через пул потоков
                target_cmd.process(chat, peer, sender, args, None, None)

    def handle_user_text_cmd(self, event):
        peer = event.object.message['peer_id']
        sender = event.object.message['from_id']
        msg = event.object.message['text'].strip()
        target_cmd = None
        if msg.startswith('!клава'):
            label = 'выбор_беседы'
            for command in self.commands:
                if command.dm and command.label == label:
                    target_cmd = command
                    break
            if target_cmd:
                target_cmd.process(-1, peer, sender, {"page_list": [0]}, None, None)
        else:
            self.kristy.send(peer, 'Для загрузки или обнуления клавиатуры, используйте команду !клава')

    def _handle_attachment(self, chat, peer, tag):
        attachment = self.kristy.db.get_attachment(chat, tag)

        if attachment:
            self.kristy.send(peer, attachment["message"], attachment["attachments"])

    def _handle_group_ping(self, chat, peer, groups, sender):
        pings_str = self.kristy.db.pings_str(chat, groups, sender)

        if pings_str:
            user_vk = self.kristy.vk.users.get(user_id=sender)
            self.kristy.send(peer,
                             user_vk[0]['first_name'] + ' ' + user_vk[0]['last_name'] + ':\n☝☝☝☝☝☝☝☝☝☝ \n' + pings_str + '\n☝☝☝☝☝☝☝☝☝☝ \n')

    def _handle_group_dm(self, chat, peer, sender, groups, message, attachments):
        sending_list = []
        sending_groups = []
        for group in groups:
            users = self.kristy.db.get_group_members(chat, group)
            if users:
                sending_groups.append(group)
                for user in users:
                    if user not in sending_list:  # добавил, что себе сообщение тоже отправляется
                        sending_list.append(user)
        if sending_list:
            user_vk = self.kristy.vk.users.get(user_id=sender, name_case='ins')
            message = re.sub(GROUP_DM_REGEX, '', message).strip()
            chat_name = self.kristy.db.get_chat_name(chat)
            response = "Отправлено" + " {0} {1} ".format(user_vk[0]["first_name"], user_vk[0][
                "last_name"]) + 'из (' + chat_name + ') для ({0}): \n'.format(', '.join(sending_groups)) + message
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

    def _did_you_mean(self, chat, peer, user_typed_name):
        """
        Пытается исправить опечатку во вводе пользователя.
        Например, если кто-то попытается написать "!врсия", бот предложит ему использовать "!версия".
        Поддерживает команды и вложения в беседах.

        :param chat: ID беседы.
        :param peer: ID беседы + 2E9.
        :param user_typed_name: Неправильное название (название с опечаткой), которое ввёл пользователь.
        """
        tags_list = self.kristy.db.get_tag_attachments(chat)
        response = ""
        for command in self.chat_command_names:
            if fuzz.ratio(user_typed_name, command) < 70:
                continue

            response += '!' + command + ' \n'
        for tag in tags_list:
            if fuzz.ratio(user_typed_name, tag) < 70:
                continue
            response += '?' + tag + ' \n'
        if response:
            self.kristy.send(peer, "💡 Возможно, вы имели в виду: \n" + response)


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

    def process(self, chat, peer, sender, args, attachments=None, fwd_messages=None):
        # noinspection PyBroadException
        if attachments is None:
            attachments = []
        if fwd_messages is None:
            fwd_messages = []
        try:
            if chat != -1 and self.kristy.db.get_user_rank_val(chat, sender) < self.min_rank.value:
                self.print_no_perm(peer)
            elif len(args) + len(attachments) + len(fwd_messages) < self.min_args:
                self.print_usage(peer)
            else:
                self.execute(chat, peer, sender, args, attachments, fwd_messages)
        except Exception:
            self.kristy.send(peer, traceback.format_exc(), ["photo-199300529_457239560"])
            traceback.print_exc()

    def execute(self, chat, peer, sender, args=None, attachments=None, fwd_messages=None):
        pass  # наследуется
