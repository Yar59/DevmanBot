import logging
from time import sleep

import requests
import telegram
from dotenv import dotenv_values


def main():
    tg_token = dotenv_values(".env")["TG_TOKEN"]
    dvmn_token = dotenv_values(".env")["DVMN_TOKEN"]
    chat_id = dotenv_values(".env")["CHAT_ID"]
    headers = {'Authorization': f'Token {dvmn_token}'}
    payload = {'timestamp': ''}
    bot = telegram.Bot(token=tg_token)
    while True:
        url = 'https://dvmn.org/api/long_polling/'
        try:
            response = requests.get(url, headers=headers, params=payload, timeout=91)
            response.raise_for_status()
            response = response.json()
            if response['status'] == 'timeout':
                payload['timestamp'] = response['timestamp_to_request']
            elif response['status'] == 'found':
                payload['timestamp'] = response['last_attempt_timestamp']
                attempts = response['new_attempts']
                for attempt in attempts:
                    if attempt['is_negative']:
                        text = f'Ваш урок "{attempt["lesson_title"]}" вернулся с проверки\n' \
                               f'Потребуются доработки :(\n' \
                               f'Посмотреть результат можно по ссылке {attempt["lesson_url"]}'
                    else:
                        text = f'Ваш урок "{attempt["lesson_title"]}" вернулся с проверки\n' \
                               f'Баги успешно спрятались :)\n' \
                               f'Посмотреть результат можно по ссылке {attempt["lesson_url"]}'
                    bot.send_message(text=text, chat_id=chat_id)
        except requests.exceptions.HTTPError as error:
            logging.warning(f'HTTPError: {error}')
        except requests.exceptions.ReadTimeout:
            logging.warning('ReadTimeout')
        except requests.exceptions.ConnectionError:
            logging.warning("Connection Error\nPlease check your internet connection")
            sleep(5)
            logging.warning("Trying to reconnect")


if __name__ == '__main__':
    main()
