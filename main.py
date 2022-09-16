import logging
import textwrap
from time import sleep

import requests
import telegram
from dotenv import dotenv_values


class TelegramLogsHandler(logging.Handler):

    def __init__(self, tg_token, chat_id):
        super().__init__()
        self.chat_id = chat_id
        self.bot = telegram.Bot(token=tg_token)

    def emit(self, record):
        log_entry = self.format(record)
        self.bot.send_message(chat_id=self.chat_id, text=log_entry)


def main():
    tg_token = dotenv_values('.env')['TG_TOKEN']
    tg_service_token = dotenv_values('.env')['TG_SERVICE_TOKEN']
    dvmn_token = dotenv_values('.env')['DVMN_TOKEN']
    chat_id = dotenv_values('.env')['CHAT_ID']

    logger = logging.getLogger('tg_logger')
    logger.setLevel(logging.WARNING)
    logger.addHandler(TelegramLogsHandler(tg_service_token, chat_id))

    headers = {'Authorization': f'Token {dvmn_token}'}
    payload = {'timestamp': ''}

    bot = telegram.Bot(token=tg_token)

    logger.warning("Bot starts")
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
        except requests.exceptions.ConnectionError:
            logger.warning('Connection Error\nPlease check your internet connection')
            sleep(5)
            logger.warning('Trying to reconnect')


if __name__ == '__main__':
    main()
