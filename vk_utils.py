import vk_api


MAX_MSG_LEN = 4096


def send(vk, peer, msg):
    """
    Отправляет указанное сообщение в указанный чат. Если длина сообщения превышает
    максимальную (MAX_MSG_LEN), то сообщение будет разбито на части и отправлено,
    соответственно, частями.

    :param vk: Клиент ВК.
    :param peer: Куда отправить сообщение (peer_id).
    :param msg: Текст сообщения.

    TODO: сделать разбиение на части более "дружелюбным" - стараться разбивать по строкам или хотя бы по пробелам.
    """
    if len(msg) <= MAX_MSG_LEN:
        vk.messages.send(peer_id=peer, message=msg, random_id=int(vk_api.utils.get_random_id()))
    else:
        chunks = (msg[k:k+MAX_MSG_LEN] for k in range(0, len(msg), MAX_MSG_LEN))

        for chunk in chunks:
            vk.messages.send(peer_id=peer, message=chunk, random_id=int(vk_api.utils.get_random_id()))
