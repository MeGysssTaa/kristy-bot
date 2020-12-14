import threading
import time

import schedule

import log_util
import timetable


logger = log_util.init_logging(__name__)


def start():
    logger.info('Запуск автоматического информатора о парах в потоке '
                + threading.current_thread().getName())
    schedule.every().minute.at(':00').do(__run)

    while True:
        schedule.run_pending()
        time.sleep(0.49)


def __run():
    groupsmgr = 1  #vk_cmds_disp.vk_cmds.groupsmgr

    for chat in groupsmgr.get_all_chats():
        #todo remove
        if chat != 1:
            continue
        #todo remove

        now = timetable.curtime(chat)

        if now is None:
            # Данные для этой беседы не были загружены.
            continue

        for group in groupsmgr.get_all_groups(chat):
            cur_ordinal = timetable.class_ordinal(chat, now)

