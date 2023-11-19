import sqlite3
from dataclasses import dataclass
from polog import log, config, file_writer

config.add_handlers(file_writer('handlers_log'))


@log
@dataclass
class DBClient:
    base_name: str = 'test_db.db'

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
