from vk_api.keyboard import VkKeyboard, VkKeyboardColor

MAX_ARGUMENTS_ON_PAGE = 6  # желательно делать чётное (огр. 1<=x<=18)


def start_keyboard(chat):
    keyboard = VkKeyboard()
    keyboard.add_button("Почта",
                        payload={"action": "почта_тег_выбор", "chat_id": chat, "args": {"page_list": [0]}},
                        color=VkKeyboardColor.PRIMARY
                        )
    keyboard.add_line()
    keyboard.add_button("Управление",
                        payload={"action": "управление", "chat_id": chat},
                        color=VkKeyboardColor.POSITIVE
                        )
    keyboard.add_line()
    keyboard.add_button("Информация",
                        payload={"action": "информация", "chat_id": chat},
                        color=VkKeyboardColor.NEGATIVE
                        )
    keyboard.add_line()
    keyboard.add_button("Развлечение",
                        payload={"action": "развлечение", "chat_id": chat}
                        )
    keyboard.add_button("Настройки",
                        payload={"action": "настройки_выбор", "chat_id": chat, "args": {"page_list": [0]}}
                        )
    return keyboard.get_keyboard()


def control_keyboard(chat):
    keyboard = VkKeyboard()
    keyboard.add_button("Подключиться к группе",
                        payload={"action": "none", "chat_id": chat, "args": {"page_list": [0]}}
                        )
    keyboard.add_button("Отключиться от группы",
                        payload={"action": "none", "chat_id": chat, "args": {"page_list": [0]}}
                        )
    keyboard.add_line()
    keyboard.add_button("Пригласить в группу",
                        payload={"action": "none", "chat_id": chat, "args": {"page_list": [0]}}
                        )
    keyboard.add_button("Кикнуть из группы",
                        payload={"action": "none", "chat_id": chat, "args": {"page_list": [0]}}
                        )
    keyboard.add_line()
    keyboard.add_button("Удалить группу",
                        payload={"action": "none", "chat_id": chat, "args": {"page_list": [0]}}
                        )
    keyboard.add_line()
    keyboard.add_button("Выход",
                        payload={"action": "стартовая_клавиатура", "chat_id": chat},
                        color=VkKeyboardColor.NEGATIVE
                        )
    return keyboard.get_keyboard()


def information_keyboard(chat):
    keyboard = VkKeyboard()
    keyboard.add_button("Все группы",
                        payload={"action": "все_группы", "chat_id": chat, "args": {"page_list": [0]}}
                        )
    keyboard.add_button("Мои группы",
                        payload={"action": "мои_группы", "chat_id": chat, "args": {"page_list": [0]}}
                        )
    keyboard.add_line()
    keyboard.add_button("Участники группы",
                        payload={"action": "участники_группы_выбор", "chat_id": chat, "args": {"page_list": [0]}}
                        )
    keyboard.add_button("Ранги участников",
                        payload={"action": "ранги_участников", "chat_id": chat, "args": {"page_list": [0]}}
                        )
    keyboard.add_line()
    keyboard.add_button("Команды",
                        payload={"action": "команда_выбор", "chat_id": chat, "args": {"page_list": [0]}}
                        )
    keyboard.add_button("Вложения",
                        payload={"action": "none", "chat_id": chat, "args": {"page_list": [0]}}
                        )
    keyboard.add_button("Статистика",
                        payload={"action": "none", "chat_id": chat, "args": {"page_list": [0]}}
                        )
    keyboard.add_line()
    keyboard.add_button("Выход",
                        payload={"action": "стартовая_клавиатура", "chat_id": chat},
                        color=VkKeyboardColor.NEGATIVE
                        )
    return keyboard.get_keyboard()

def choose_keyboard(chat, response, arguments, page_list, action_to, action_now, action_from=None, parameter=None):
    """
    chat - id беседы (int)
    response - сообщение, которое показывается при загрузке клавиатуры (str)
    argument - массив массивов с параметром name (название кнопки) и arg (что будет в argument)
    page_list - массив последовательности страниц. Нужна для 2+ углубления (list int)
    action_to - функция, которая будет выполняться при нажатии на кнопки (str)
    action_now - функция, которая происходит сейчас (нужна для перелистывания между страницами) (str)
    action_from - функция, которая вызвала текущую функцию (нужна для кнопки выход). Если отсутствует, то кнопка выход не появляется (str)
    parameter - параметр, который нужен для 2 углубления (str) TODO сделать потом list, как с page, чтобы можно было 3+
    return - новый response и клавиатура (уже json)
    """
    page_now = page_list[-1]
    if page_now > (len(arguments) - 1) // MAX_ARGUMENTS_ON_PAGE:
        page_now = 0
    elif page_now < 0:
        page_now = (len(arguments) - 1) // MAX_ARGUMENTS_ON_PAGE
    keyboard = VkKeyboard()
    for number, argument in enumerate(arguments[page_now * MAX_ARGUMENTS_ON_PAGE:(
            page_now * MAX_ARGUMENTS_ON_PAGE + MAX_ARGUMENTS_ON_PAGE) if page_now * MAX_ARGUMENTS_ON_PAGE + MAX_ARGUMENTS_ON_PAGE <= len(arguments) else len(arguments)]):
        if number % 2 == 0 and number != 0:
            keyboard.add_line()
        keyboard.add_button(argument[0],
                            payload={'action': action_to, 'chat_id': chat, 'args': {'argument': argument[1],
                                                                                    'parament': parameter,
                                                                                    'page_list': page_list}})
    if MAX_ARGUMENTS_ON_PAGE < len(arguments) or action_from:
        keyboard.add_line()
    if MAX_ARGUMENTS_ON_PAGE < len(arguments):
        response += ' \nCтр. ' + str(page_now + 1) + '/' + str((len(arguments) - 1) // MAX_ARGUMENTS_ON_PAGE + 1)
        keyboard.add_button('Назад',
                            color=VkKeyboardColor.PRIMARY,
                            payload={'action': action_now, 'chat_id': chat, 'args': {'parament': parameter,
                                                                                     'page_list': page_list[:-1] + [page_now - 1]}})
    if action_from:
        keyboard.add_button('Выход',
                            color=VkKeyboardColor.NEGATIVE,
                            payload={'action': action_from, 'chat_id': chat, 'args': {'page_list': page_list[:-1]}})
    if MAX_ARGUMENTS_ON_PAGE < len(arguments):
        keyboard.add_button('Далее',
                            color=VkKeyboardColor.PRIMARY,
                            payload={'action': action_now, 'chat_id': chat, 'args': {'parament': parameter,
                                                                                     'page_list': page_list[:-1] + [page_now + 1]}})

    return response, keyboard.get_keyboard()
