from dataclasses import dataclass
from database.handlers.db_client import DBClient


@dataclass()
class GroupClient(DBClient):
    def __init__(self, base_name: str = 'test_db'):
        super().__init__(base_name)

    def add_user(self, user_id: int, user_to_add_id: int) -> str:
        if not self.__check_unaccepted_request(user_id, user_to_add_id):
            query = f'insert into users_groups values ({user_id}, {user_to_add_id}, {0})'
            answer = 'Заявка зафиксирована. Подождите когда пользователь проделает аналогичные действия со своей стороны'
        else:
            query = f'update users_groups set is_accepted = 1 where user_1 = {user_to_add_id} and user_1 = {user_id}'
            answer = 'Группа успешно сформирована. Управлять общими показами можно в разделе "Группы"'
        cursor, conn = self._send_query(query)
        conn.commit()
        conn.close()
        return answer

    def delete_user(self, user_1_id: int, user_2_id: int) -> str:
        if self.__check_exists_groups(user_1_id, user_2_id):
            query = f'delete from users_groups where user_1 in ({user_1_id}, {user_2_id}) and user_2 in ({user_1_id}, {user_2_id})'
            cursor, conn = self._send_query(query)
            conn.commit()
            conn.close()
            answer = 'Группа успешно расформирована'
        else:
            answer = f'Общей группы с пользователем @{user_2_id} не обнаружено'
        return answer

    def __check_unaccepted_request(self, user_id: int, user_to_add_id: int) -> bool:
        query = f'select count(*) from users_groups where user_1 = {int(user_to_add_id)} and user_2 = {int(user_id)}'
        cursor, conn = self._send_query(query)
        result = cursor.fetchone()[0]
        conn.close()
        return bool(result)

    def __check_exists_groups(self, user_1_id: int, user_2_id: int) -> bool:
        query = (f'''select count(*) from users_groups
                 where user_1 in ({user_1_id}, {user_2_id})
                 and user_2 in ({user_1_id}, {user_2_id}) and is_accepted = 1''')
        cursor, conn = self._send_query(query)
        result = cursor.fetchone()[0]
        conn.close()
        return bool(result)
