import sqlite3
import pandas as pd
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
            conn.close()
            return True
        else:
            conn.close()
            return False


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

    def get_user(self, user_id: int, vision: bool = False):
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


@dataclass
class ExpenseClient(DBClient):

    def __init__(self, base_name: str = 'test_db'):
        super().__init__(base_name)

    def add_expense(self, expense: dict):
        query = f'''insert into expenses (user_id, category, subcategory, expenses_sum, tags, report_date)
                   values ({expense['user_id']}, "{expense['category']}", "{expense['subcategory']}",
                            {expense['expenses_sum']}, "{expense['tags']}", "{expense['report_date']}")'''
        cursor, conn = self._send_query(query)
        conn.commit()
        conn.close()

    def get_statistics(self, period: str = 'monthly', interval: str = None):
        cur_interval = ''
        filter = ''
        if period == 'daily':
            if interval:
                cur_interval = f", '{interval} days'"
            filter = f"where report_date = date(date() {cur_interval})"
        elif period == 'weekly':
            if interval:
                cur_interval = f", '{int(interval) * 7} days'"
            filter = f"where strftime('%W', report_date) = strftime('%W', 'now' {cur_interval})"
        elif period == 'monthly':
            if interval:
                cur_interval = f", '{interval} months'"
            filter = f"where date(report_date, 'start of month') = date(date(), 'start of month' {cur_interval})"
        elif period == 'yearly':
            if interval:
                cur_interval = f", {interval} years'"
            filter = f"where strftime('%Y', report_date) = strftime('%Y', 'now' {cur_interval})"
        query = f'''select category, sum(expenses_sum) as total_sum, count(expenses_sum) as total_count 
                    from expenses {filter} group by category'''
        cursor, conn = self._send_query(query)
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df


@dataclass
class LimitClient(DBClient):
    def __init__(self, base_name: str = 'test_db'):
        super().__init__(base_name)

    def add_limit(self, user_id: str, category: str, limit: int):
        if self._check_exists(f'''select * from limits where user_id = {user_id} and category = '{category}' '''):
            return 'already exist'
        else:
            query = f'''insert into limits (user_id, category, cat_limit) values ({user_id}, '{category}', {int(limit)})'''
            print(query)
            cursor, conn = self._send_query(query)
            conn.commit()
            conn.close()
            return 'success'

    def get_limits(self, user_id: str):
        query = f'select * from limits where user_id = {user_id}'
        cursor, conn = self._send_query(query)
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df

    def delete_limit(self, user_id: str, category: str):
        query = f'''delete from limits where user_id = {user_id} and category = '{category}' '''
        cursor, conn = self._send_query(query)
        conn.commit()
        conn.close()

    def update_limit(self, user_id: str, category: str, limit: int):
        query = f'''update limits set cat_limit = {limit} where user_id = {user_id} and category = '{category}' '''
        cursor, conn = self._send_query(query)
        conn.close()
