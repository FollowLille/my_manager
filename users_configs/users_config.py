from dataclasses import dataclass
import json


@dataclass
class UsersLib:

    @classmethod
    def add_new_user(cls, user_id, name):
        known_users = cls.get_users()
        known_users[user_id]["name"] = name
        known_users[user_id]["vision"] = 'my'
        with open('my_manager/users_configs/users.json', 'w', encoding='utf-8') as file:
            json.dump(known_users, file, ensure_ascii=False)

    @staticmethod
    def get_users():
        with open('my_manager/users_configs/users.json', 'r', encoding='utf-8') as file:
            known_users = json.load(file)
        return known_users

    @classmethod
    def change_name(cls, user_id: int, new_name: str):
        with open('my_manager/users_configs/users.json', 'r', encoding='utf-8') as file:
            known_users = json.load(file)
        known_users[f'{user_id}']['name'] = new_name
        with open('my_manager/users_configs/users.json', 'w', encoding='utf-8') as file:
            json.dump(known_users, file, ensure_ascii=False)

    @classmethod
    def change_vision(cls, user_id: int, rule: str):
        with open('my_manager/users_configs/users.json', 'r', encoding='utf-8') as file:
            known_users = json.load(file)
        known_users[f'{user_id}']['vision'] = rule
        with open('my_manager/users_configs/users.json', 'w', encoding='utf-8') as file:
            json.dump(known_users, file, ensure_ascii=False)
