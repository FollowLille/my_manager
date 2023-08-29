from dataclasses import dataclass
import json


@dataclass()
class ReplaceDict:

    @staticmethod
    def _get_dict(file_name: str) -> dict:
        with open(f'{file_name}.json', 'r', encoding='utf-8') as file:
            _dict = json.load(file)
        return _dict

    @staticmethod
    def _save_dict(file_name: str, _dict: dict) -> None:
        with open(f'{file_name}.json', 'w', encoding='utf-8') as file:
            json.dump(_dict, file, ensure_ascii=False)

    @staticmethod
    def _get_last_value(_dict: dict) -> int:
        if _dict:
            return _dict.get(max(_dict, key=_dict.get))
        else:
            return 0

    def get_value_by_key(self, key: str, file_name: str) -> str:
        _dict = self._get_dict(file_name)
        return _dict.get(key)

    def get_key_by_value(self, value: int, file_name: str) -> str:
        if isinstance(value, str):
            value = int(value)
        _dict = self._get_dict(file_name)
        return list(_dict.keys())[list(_dict.values()).index(value)]

    def add_new_key(self, key: str, file_name: str) -> None:
        _dict = self._get_dict(file_name)
        last_value = self._get_last_value(_dict)
        _dict[key] = last_value + 1
        self._save_dict(file_name, _dict)

    def convert(self, key: str, file_name: str) -> str:
        _dict = self._get_dict(file_name)
        if _dict.get(key):
            return self.get_value_by_key(key, file_name)
        else:
            self.add_new_key(key, file_name)
            _dict = self._get_dict(file_name)
            return self.get_value_by_key(key, file_name)

    def revers_convert(self, value: int, file_name: str) -> str:
        _dict = self._get_dict(file_name)
        return self.get_key_by_value(value, file_name)

    def list_convert(self, _list: list, file_name: str) -> list:
        return [self.convert(key, file_name) for key in _list]

    def revers_list_convert(self, _list: list, file_name: str) -> list:
        _list = [int(num) for num in _list]
        return [self.revers_convert(value, file_name) for value in _list]
