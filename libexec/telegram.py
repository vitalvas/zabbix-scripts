#!/opt/python/zabbix/bin/python

import requests

class Telegram:
    def __init__(self, config: dict, prefix: str = None) -> None:
        self.config = config
        self.prefix = prefix

    def send_message(self, message: str) -> None:
        bot_token = self.config.get('bot_token')
        api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

        for chat in self.config.get('chat_ids', []):
            chat_text = message
            if self.prefix:
                chat_text = f'{self.prefix} {message}'
            params = {
                'chat_id': chat,
                'text': chat_text,
                'parse_mode': 'HTML',
            }
            response = requests.post(api_url, params=params)
            response.raise_for_status()

