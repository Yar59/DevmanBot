import logging
import textwrap
from time import sleep

import requests
import telegram
from environs import Env


class TelegramLogsHandler(logging.Handler):

    def __init__(self, tg_token, chat_id):
        super().__init__()
        self.chat_id = chat_id
        self.bot = telegram.Bot(token=tg_token)

    def emit(self, record):
        log_entry = self.format(record)
        self.bot.send_message(chat_id=self.chat_id, text=log_entry)


def main():
    env = Env()
    env.read_env()
    tg_token = env('TG_TOKEN')
    second_bot = env.bool('SECOND_BOT', False)
    dvmn_token = env('DVMN_TOKEN')
    chat_id = env('CHAT_ID')

    logger = logging.getLogger('tg_logger')
    logger.setLevel(logging.WARNING)
    if second_bot:
        tg_service_token = env('TG_SERVICE_TOKEN')
        logger.addHandler(TelegramLogsHandler(tg_service_token, chat_id))

    headers = {'Authorization': f'Token {dvmn_token}'}
    payload = {'timestamp': ''}

    bot = telegram.Bot(token=tg_token)

    logger.warning("Бот успешно запущен")

    while True:
        url = 'https://dvmn.org/api/long_polling/'
        try:
            response = requests.get(url, headers=headers, params=payload, timeout=91)
            response.raise_for_status()
            changes = response.json()

            if changes['status'] == 'timeout':
                payload['timestamp'] = changes['timestamp_to_request']
            elif changes['status'] == 'found':
                payload['timestamp'] = changes['last_attempt_timestamp']
                attempts = changes['new_attempts']
                for attempt in attempts:
                    if attempt['is_negative']:
                        text = f'''\
                            Ваш урок "{attempt["lesson_title"]}" вернулся с проверки 
                            Потребуются доработки :(
                            Посмотреть результат можно по ссылке {attempt["lesson_url"]}'''
                    else:
                        text = f'''\
                            Ваш урок "{attempt["lesson_title"]}" вернулся с проверки' 
                            Баги успешно спрятались :)
                            Посмотреть результат можно по ссылке {attempt["lesson_url"]}'''

                    bot.send_message(text=textwrap.dedent(text), chat_id=chat_id)

        except requests.exceptions.HTTPError as error:
            logger.warning(f'HTTPError: {error}')
        except requests.exceptions.ReadTimeout:
            logger.warning('ReadTimeout')
        except telegram.error.TimedOut:
            logging.warning("Не удалось отправить сообщение в телеграмм")
        except requests.exceptions.ConnectionError:
            logging.warning('Connection Error\nPlease check your internet connection')
            sleep(5)
            logging.warning('Trying to reconnect')


if __name__ == '__main__':
    main()
