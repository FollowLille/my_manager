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
        return _dict.get(max(_dict, key=_dict.get))

    def get_value_by_key(self, key: str, file_name: str) -> str:
        _dict = self._get_dict(file_name)
        if 'category' in file_name:
            return _dict[key].get('id')
        else:
            return _dict.get(key)

    def get_key_by_value(self, value: str, file_name: str) -> str:
        if isinstance(value, str):
            value = int(value)
        _dict = self._get_dict(file_name)
        if 'category' in file_name:
            id_list = [value.get('id') for value in _dict.values()]
            return list(_dict.keys())[id_list.index(value)]
        else:
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

    def reverse_convert(self, value: str, file_name: str) -> str:
        _dict = self._get_dict(file_name)
        return self.get_key_by_value(value, file_name)

    def list_convert(self, _list: list, file_name: str) -> list:
        return [self.convert(key, file_name) for key in _list]

    def reverse_list_convert(self, _list: list, file_name: str) -> list:
        return [self.reverse_convert(value, file_name) for value in _list]

    def convert_subcategories(self, category: str, key: str, file_name: str) -> list:
        _dict = self._get_dict(file_name)
        sub_category = _dict.get(category).get('sub_categories').get(key)
        return [sub_category['parent_id'], sub_category['child_id']]

    def reverse_convert_subcategories(self, category: str, sub_category: str, file_name: str) -> list:
        _dict = self._get_dict(file_name)
        id_list = [value.get('id') for value in _dict.values()]
        category = list(_dict.keys())[id_list.index(int(category))]
        sub_category_dict = _dict.get(category).get('sub_categories')
        sub_id_list = [value.get('child_id') for value in sub_category_dict.values()]
        sub_category = list(sub_category_dict.keys())[sub_id_list.index(int(sub_category))]
        return [category, sub_category]
