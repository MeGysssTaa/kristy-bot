import logging
import logging.handlers
import logging.config
import os
import time
import traceback

import yaml


def init_logging(module):
    print('Настройка журналирования для модуля ' + module)

    if not os.path.exists('logs'):
        os.mkdir('logs/')

    with open('logging.cfg.yml', 'r', encoding='UTF-8') as fstream:
        # noinspection PyBroadException
        try:
            logging.config.dictConfig(yaml.safe_load(fstream))
            logger = logging.getLogger(module)

            # Т.к. suffix нельзя установить через конфиг, приходится делать так...
            for handler in logger.handlers:
                if type(handler) == logging.handlers.TimedRotatingFileHandler:
                    handler.suffix = '%Y.%m.%d.log'

            return logger
        except Exception:
            print('\n\n\nНе удалось настроить журналирование для модуля \"%s\":' % module)
            traceback.print_exc()
            print('\n\n\nВыход через 5 секунд...')
            time.sleep(5)
            print('\n\n\nВыход')
            exit(1)
