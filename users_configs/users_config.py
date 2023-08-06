from dataclasses import dataclass
import json

@dataclass
class UsersLib:

    @classmethod
    def add_new_user(cls, id, name):
        known_users = cls.get_users()
        known_users[id] = name
        with open('my_manager/users_configs/users.json', 'w', encoding='utf-8') as file:
            json.dump(known_users, file, ensure_ascii=False)

    @staticmethod
    def get_users():
        with open('my_manager/users_configs/users.json', 'r', encoding='utf-8') as file:
            known_users = json.load(file)
        return known_users

