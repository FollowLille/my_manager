import sqlite3
from dataclasses import dataclass


@dataclass
class DBClient:

    def __init__(self, base_name: str = 'test_db'):
        self.base_name = base_name + '.db'

    def _get_cursor(self) -> sqlite3.Connection.cursor:
        conn = sqlite3.connect(self.base_name)
        cursor = conn.cursor()
        return cursor, conn

    def _send_query(self, query: str, values: dict = None, is_many: bool = False):
        cursor, conn = self._get_cursor()
        if not is_many:
            if values:
                cursor.execute(query, values)
            else:
                cursor.execute(query)
        else:
            if values:
                cursor.executemany(query, values)
            else:
                cursor.executemany(query)
        return cursor, conn

    def _check_exists(self, query: str) -> bool:
        cursor, conn = self._get_cursor()
        result = cursor.execute(query)
        if result.fetchall():
            return True
        else:
            return False


@dataclass
class UserClient(DBClient):
    def __init__(self, base_name: str = 'test_db'):
        super().__init__(base_name)

    def add_user(self, user_id: int, name: str):
        query = 'insert into users values(:user_id, :name, :vision)'
        values = {"user_id": user_id, "name": name, "vision": "mine"}
        if not self._check_exists(f'select * from users where user_id = {user_id}'):
            cursor, conn = self._send_query(query=query, values=values)
            conn.commit()
            conn.close()
        else:
            print('Такой пользователь уже существует')

    def get_users(self):
        query = 'select * from users'
        cursor, conn = self._send_query(query)
        result = cursor.fetchall()
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


@dataclass
class ExpenseClient(DBClient):

    def __init__(self, base_name: str = 'test_db'):
        super().__init__(base_name)

    def add_expense(self, expense: dict):
        query = f'''insert into expenses (user_id, category, subcategory, cur_sum, tags, report_date)
                   values ({expense['user_id']}, "{expense['category']}", "{expense['subcategory']}",
                            "{expense['cur_sum']}", "{expense['tags']}", "{expense['report_date']}")'''
        print(query)
        cursor, conn = self._send_query(query)
        conn.commit()
        conn.close()

    def get_expenses(self):
        query = 'select * from expenses'
        filter = 'where'
        cursor, conn = self._send_query(query)
        result = cursor.fetchall()
        conn.commit()
        conn.close()
        return result
