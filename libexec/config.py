#!/opt/python/zabbix/bin/python

import json
import os
from pathlib import Path


class Config:
    def __init__(self) -> None:
        self.config_file = os.path.join(
            os.path.dirname(Path(__file__).resolve().parent),
            "config.json"
        )
        self.__config = None

    def get(self, item: str) -> dict:
        if not self.__config:
            with open(self.config_file) as f:
                self.__config = json.load(f)

        return self.__config.get(item)

    def __getitem__(self, item: str):
        return self.get(item)

