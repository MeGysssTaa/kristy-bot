import json
import threading
import traceback


from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
import re
import vk_cmds

forbidden_names = re.compile(r"(?:\s|^)" + "(@" + ")|(@".join(vk_cmds.FORBIDDEN_NAMES) + ")" + "(?=[\s .,:;?()!]|$)")


class VkCmdsDispatcher(threading.Thread):
    def __init__(self, longpoll, commands):
        super(VkCmdsDispatcher, self).__init__()

        self.daemon = True
        self.longpoll = longpoll
        self.commands = commands

    def run(self):
        for event in self.longpoll.listen():
            if event.type == VkBotEventType.MESSAGE_NEW:
                if event.from_chat:
                    self.__from_chat(event)
                elif event.from_user and 'payload' in event.object.message:
                    self.__from_user_keyboard(event)
                elif event.from_user:
                    self.__from_user_text(event)
                    pass

    def __from_chat(self, event):
        """
        Обработка команд в беседе.
        """
        pass

    def __from_user_keyboard(self, event):
        """
        Обработка команд в ЛС бота (кнопки).
        """
        payload = json.loads(event.object.message['payload'])
        sender = event.object.message['from_id']
        peer = event.object.message['peer_id']
        if 'action' not in payload or 'chat_id' not in payload:
            return
        chat = payload['chat_id']
        label = payload['action']
        if chat == -1 and label != 'выбор_беседы':
            # TODO: здесь попросить выбрать беседу (через кнопки) вместо pass
            vk_cmds.exec_choose_chat_keyboard(None, chat, peer, sender, [0])
            pass
        # обработчик от мамкиных хакеров
        elif chat != -1 and sender not in vk_cmds.groupsmgr.get_users(chat):
            return
        else:
            target_cmd = None

            args = payload['args'] if 'args' in payload else []
            for command in self.commands:
                if command.dm and command.label == label:
                    target_cmd = command
                    break

            if target_cmd is not None:
                # TODO (совсем потом) выполнять команды асинхронно - через пул потоков
                target_cmd.execute(chat, peer, sender, args)

    def __from_user_text(self, event):
        sender = event.object.message['from_id']
        peer = event.object.message['peer_id']
        msg = event.object.message['text'].strip()

        if msg.startswith('!клавиатура'):
            vk_cmds.exec_choose_chat_keyboard(None, -1, peer, sender, [0])
        else:
            vk_cmds.send(peer, 'Для загрузки или обнуления клавиатуры, используйте команду !клавиатура')


class VkChatCmd:
    def __init__(self, label, desc, exec_func,
                 min_rank=vk_cmds.Rank.WORKER, usage=None, min_args=0, dm=False, attachments=False):
        self.label = label
        self.usage = usage
        self.desc = desc
        self.min_args = min_args
        self.exec_func = exec_func
        self.dm = dm
        self.min_rank = min_rank
        self.attachments = attachments

    def print_usage(self, peer):
        if self.usage is not None:
            self.send(peer, '⚠ Использование: \n' + self.usage)

    def print_error_rank(self, peer):
        self.send(peer, '⛔ Нет прав ⛔')

    def send(self, peer, msg, attachment=None):  # если я перенёс send в vk_cmds, то мб это убрать?
        vk_cmds.send(peer, msg, attachment)

    def execute(self, chat, peer, sender, args, attachments=False):
        # noinspection PyBroadException
        try:
            if chat != -1 and vk_cmds.Rank[vk_cmds.groupsmgr.get_rank_user(chat, sender)].value < self.min_rank.value:  # и тут глаза Германа ушли в запой или взапой, не знаю
                self.print_error_rank(peer)
            elif len(args) < self.min_args:
                self.print_usage(peer)
            else:
                if self.min_args > 0:
                    if self.attachments:
                        self.exec_func(self, chat, peer, sender, args, attachments)
                    else:
                        self.exec_func(self, chat, peer, sender, args)
                else:
                    if self.attachments:
                        self.exec_func(self, chat, peer, sender, attachments)
                    else:
                        self.exec_func(self, chat, peer, sender)
        except Exception:
            self.send(peer, 'Ты чево наделол......\n\n' + traceback.format_exc())


def start(longpoll):
    """
    Запускает обработчик команд ВК в беседах.
    """
    commands = register_cmds()
    dispatcher = VkCmdsDispatcher(longpoll, commands)
    dispatcher.start()


def register_cmds():
    return (
        VkChatCmd(
            label='пара',
            desc='Отображает информацию о следующей паре. Эта информация может зависеть '
                 'от того, в каких группах находится использовавший эту команду.',
            exec_func=vk_cmds.exec_next_class
        ),
        VkChatCmd(
            label='создать',
            desc='Создать новую группу.',
            usage='!создать <группа1> [группа2] [...] [группаN]',
            min_args=1,
            exec_func=vk_cmds.exec_create,
            min_rank=vk_cmds.Rank.USER
        ),
        VkChatCmd(
            label='удалить',
            desc='Удалить группу.',
            usage='!удалить <группа1> [группа2] [...] [группаN]',
            min_args=1,
            exec_func=vk_cmds.exec_delete,
            min_rank=vk_cmds.Rank.MODERATOR
        ),
        VkChatCmd(
            label='подключиться',
            desc='Подключает вас к указанной группе.',
            usage='нажми на любою другую работающую кнопку',
            min_args=1,
            exec_func=vk_cmds.exec_join,
            dm=True
        ),
        VkChatCmd(
            label='отключиться',
            desc='Отключает вас от указанной группы.',
            usage='нажми на любою другую работающую кнопку',
            min_args=1,
            exec_func=vk_cmds.exec_left,
            dm=True
        ),
        VkChatCmd(
            label='подключить',
            desc='Подключает указанных людей к указанным группам.',
            usage='!подключить <@юзер1> [@юзер2] [...] [@юзерN] > <группа1> [группа2] [...] [группаM]',
            min_args=3,
            exec_func=vk_cmds.exec_join_members,
            min_rank=vk_cmds.Rank.MODERATOR
        ),
        VkChatCmd(
            label='отключить',
            desc='Отключает указанных людей от указанных групп.',
            usage='!отключить <@юзер1> [@юзер2] [...] [@юзерN] > <группа1> [группа2] [...] [группаM]',
            min_args=3,
            exec_func=vk_cmds.exec_left_members,
            min_rank=vk_cmds.Rank.MODERATOR
        ),
        VkChatCmd(
            label='переименовать',
            desc='Меняет название группы.',
            usage='!переименовать <старое_название> <новое_название>',
            min_args=2,
            exec_func=vk_cmds.exec_rename,
            min_rank=vk_cmds.Rank.MODERATOR
        ),
        VkChatCmd(
            label='неделя',
            desc='Отображает информацию о чётности текущей недели.',
            exec_func=vk_cmds.exec_week
        ),
        VkChatCmd(
            label='рулетка',
            desc='Выбирает случайного участника беседы и выводит его фото.',
            exec_func=vk_cmds.exec_roulette,
            min_rank=vk_cmds.Rank.PRO
        ),
        VkChatCmd(
            label='вложение+',
            desc='Создаёт новый тег и привязывает к нему текст и/или вложения.',
            usage='!вложение+ <тег> [текст] // Чтобы добавить вложения, прикрепите их к сообщению с командой (максимум 4)',
            min_args=1,
            exec_func=vk_cmds.exec_add_one_attachment,
            min_rank=vk_cmds.Rank.PRO,
            attachments=True
        ),
        VkChatCmd(
            label='вложение++',
            desc='Создаёт несколько новых тегов и привязывает к ним вложения',
            usage='!вложение++ <тег1> [тег2] [тег3] [тег4] // Чтобы добавить вложения, прикрепите их к сообщению с командой (максимум 4)',
            min_args=1,
            exec_func=vk_cmds.exec_add_many_attachments,
            min_rank=vk_cmds.Rank.PRO,
            attachments=True
        ),
        VkChatCmd(
            label='вложение*',
            desc='Изменяет текст и/или вложения, привязанные к уже существующему тегу.',
            usage='!вложение* <тег> [текст] // Чтобы добавить вложения, прикрепите их к сообщению с командой (максимум 4)',
            min_args=1,
            exec_func=vk_cmds.exec_edit_attachment,
            min_rank=vk_cmds.Rank.PRO,
            attachments=True
        ),
        VkChatCmd(
            label='вложение-',
            desc='Удаляет тег.',
            usage='!вложение- <тег1> [тег2] ... [тегN]',
            min_args=1,
            exec_func=vk_cmds.exec_remove_attachment,
            min_rank=vk_cmds.Rank.PRO
        ),
        VkChatCmd(
            label='ранг',
            desc='Изменяет ранг выбранных пользователей.',
            usage='!ранг <название_ранга> <@юзер1> [@юзер2] ... [@юзерN]',
            min_args=2,
            exec_func=vk_cmds.exec_change_rank,
            min_rank=vk_cmds.Rank.MODERATOR
        ),
        VkChatCmd(
            label='name',
            desc='Меняет название беседы в базе данных бота.',
            usage='!name <новое_название>',
            min_args=1,
            exec_func=vk_cmds.exec_change_name_chat,
            min_rank=vk_cmds.Rank.ADMIN
        ),
        VkChatCmd(
            label='руслан',
            desc='Руслан, просто Руслан.',
            usage='!руслан',
            exec_func=vk_cmds.exec_ruslan,
            min_rank=vk_cmds.Rank.PRO
        ),
        VkChatCmd(
            label='выбор',
            desc='Выбирает указанное число случайных участников беседы.',
            usage='!выбор <число_участников>',
            min_args=1,
            exec_func=vk_cmds.exec_choose,
            min_rank=vk_cmds.Rank.PRO
        ),
        VkChatCmd(
            label='ворота',
            desc='Отображает время до открытия или до закрытия ворот.',
            exec_func=vk_cmds.exec_gate
        ),
        VkChatCmd(
            label='бфу',
            desc='Показывает всю красоту БФУ (локальные мемы в массы).',
            usage='!бфу',
            exec_func=vk_cmds.  exec_bfu
        ),
        VkChatCmd(
            label='почта',
            desc='Добавляет событие к существующей почте по тегу.',
            usage='!почта <тег> <дата ДД.ММ> or <дата_время ДД.ММ:ЧЧ.ММ> [текст] // Чтобы добавить вложения, прикрепите их к сообщению с командой (максимум 4)',
            min_args=2,
            exec_func=vk_cmds.exec_add_event_to_email,
            min_rank=vk_cmds.Rank.USER,
            attachments=True
        ),
        VkChatCmd(
            label='почта+',
            desc='Создаёт новые теги для почты.',
            usage='!почта+ <тег1> [тег2] ... [тегN]',
            min_args=1,
            exec_func=vk_cmds.exec_create_emails,
            min_rank=vk_cmds.Rank.PRO
        ),
        VkChatCmd(
            label='почта-',
            desc='Удаляет теги для почты.',
            usage='!почта- <тег1> [тег2] ... [тегN]',
            min_args=1,
            exec_func=vk_cmds.exec_delete_emails,
            min_rank=vk_cmds.Rank.MODERATOR
        ),
        VkChatCmd(
            label='выбор_беседы',
            desc='Выбор активной беседы',
            usage='???',
            min_args=1,
            exec_func=vk_cmds.exec_choose_chat_keyboard,
            dm=True,
            min_rank=vk_cmds.Rank.GOVNO
        ),
        VkChatCmd(
            label='стартовая_клавиатура',
            desc='Отправить стартовую клавиатуру',
            usage='???',
            exec_func=vk_cmds.exec_send_start_keyboard,
            dm=True,
            min_rank=vk_cmds.Rank.GOVNO
        ),
        VkChatCmd(
            label='все_группы',
            desc='Показывает все группы в беседе',
            usage='???',
            exec_func=vk_cmds.exec_all_groups,
            dm=True
        ),
        VkChatCmd(
            label='мои_группы',
            desc='Показывает мои группы в беседе',
            usage='???',
            exec_func=vk_cmds.exec_my_groups,
            dm=True
        ),
        VkChatCmd(
            label='состав_группы_выбор',
            desc='Выбор группы для отображения участников группы',
            usage='???',
            min_args=1,
            exec_func=vk_cmds.exec_choose_members_group,
            dm=True
        ),
        VkChatCmd(
            label='состав_группы',
            desc='Показывает участников выбранной группы',
            usage='???',
            min_args=1,
            exec_func=vk_cmds.exec_members_group,
            dm=True
        ),
        VkChatCmd(
            label='почта_выбор_тег',
            desc='Выбор тега почты',
            usage='???',
            min_args=1,
            exec_func=vk_cmds.exec_choose_tag_email,
            dm=True
        ),
        VkChatCmd(
            label='почта_выбор_события',
            desc='Выбор события в почте',
            usage='???',
            min_args=2,
            exec_func=vk_cmds.exec_choose_events_email,
            dm=True
        ),
        VkChatCmd(
            label='событие',
            desc='Выводит событие',
            usage='???',
            min_args=2,
            exec_func=vk_cmds.exec_event_email,
            dm=True
        ),
        VkChatCmd(
            label='подключиться_выбор',
            desc='Выбор группы для подключения',
            usage='нажми на любою другую работающую кнопку',
            min_args=1,
            exec_func=vk_cmds.exec_choose_join_group,
            dm=True
        ),
        VkChatCmd(
            label='отключиться_выбор',
            desc='Выбор группы для отключения',
            usage='нажми на любою другую работающую кнопку',
            min_args=1,
            exec_func=vk_cmds.exec_choose_left_group,
            dm=True
        ),
        VkChatCmd(
            label='настройки_выбор',
            desc='Выбор настроек',
            usage='???',
            exec_func=vk_cmds.exec_choose_settings,
            dm=True
        ),
        VkChatCmd(
            label='all',
            desc='Показать топ 5 предателей',
            usage='!all',
            exec_func=vk_cmds.exec_alls
        )

    )
