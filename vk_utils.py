import vk_api


# Ограничение ВК на максимальную длину сообщения (в символах).
MAX_MSG_LEN = 4096


def send(vk, peer, msg, attachment=None):
    """
    Отправляет указанное сообщение в указанный чат. Если длина сообщения превышает
    максимальную (MAX_MSG_LEN), то сообщение будет разбито на части и отправлено,
    соответственно, частями.

    :param vk: Клиент ВК.
    :param peer: Куда отправить сообщение (peer_id).
    :param msg: Текст сообщения.
    :param attachment: Вложения

    TODO: сделать разбиение на части более "дружелюбным" - стараться разбивать по строкам или хотя бы по пробелам.
    """
    if len(msg) <= MAX_MSG_LEN:
        vk.messages.send(peer_id=peer, message=msg, attachment=attachment, random_id=int(vk_api.utils.get_random_id()))
    else:
        chunks = (msg[k:k+MAX_MSG_LEN] for k in range(0, len(msg), MAX_MSG_LEN))

        for chunk in chunks:
            vk.messages.send(peer_id=peer, message=chunk, random_id=int(vk_api.utils.get_random_id()))
