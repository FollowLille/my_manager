from dataclasses import dataclass
from database.handlers.db_client import DBClient


@dataclass
class UserClient(DBClient):
    def __init__(self, base_name: str = 'test_db'):
        super().__init__(base_name)

    def add_user(self, user_id: int, name: str):
        query = 'insert into users values(:user_id, :name, :vision)'
        values = {"user_id": user_id, "name": name, "vision": "my"}
        if not self._check_exists(f'select * from users where user_id = {user_id}'):
            cursor, conn = self._send_query(query=query, values=values)
            conn.commit()
            conn.close()
        else:
            print('Такой пользователь уже существует')

    def get_user(self, user_id: int, vision: bool = False) -> str:
        if not vision:
            query = f'select name from users where user_id = {user_id}'
        else:
            query = f'select vision from users where user_id = {user_id}'
        cursor, conn = self._send_query(query)
        result = cursor.fetchone()
        conn.commit()
        conn.close()
        return result

    def change_user_info(self, user_id: int, user_name: str = None, vision: str = None):
        if user_name and vision:
            query = f'update users set name = "{user_name}" and vision = "{vision}" where user_id = {user_id}'
        elif user_name:
            query = f'update users set name = "{user_name}" where user_id = {user_id}'
        else:
            query = f'update users set vision = "{vision}" where user_id = {user_id}'
        cursor, conn = self._send_query(query)
        conn.commit()
        conn.close()
