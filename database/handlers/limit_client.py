import sqlite3
from typing import List, Any
import pandas as pd
from dataclasses import dataclass
from database.handlers.db_client import DBClient


@dataclass
class LimitClient(DBClient):
    def __init__(self, base_name: str = 'test_db'):
        super().__init__(base_name)

    def add_limit(self, user_id: str, category: str, limit: int) -> str:
        if self._check_exists(f'''select * from limits where user_id = {user_id} and category = '{category}' '''):
            return 'already exist'
        else:
            query = f'''insert into limits (user_id, category, cat_limit) values ({user_id}, '{category}', {int(limit)})'''
            cursor, conn = self._send_query(query)
            conn.commit()
            conn.close()
            return 'success'

    def get_limits(self, user_id: str) -> pd.DataFrame:
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
