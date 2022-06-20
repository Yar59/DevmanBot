import logging
from time import sleep
from pprint import pprint  # отладочный импорт
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
            response = requests.get(url, headers=headers, timeout=91)
            pprint(response.json())
            response.raise_for_status()
            response = response.json()
            if response['status'] == 'timeout':
                payload['timestamp'] = response['timestamp_to_request']
            elif response['status'] == 'found':
                attempts = response['new_attempts']
                for attempt in attempts:
                    text = f'has new attempt {attempt}'
                    bot.send_mesage(text=text, chat_id=chat_id)
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
