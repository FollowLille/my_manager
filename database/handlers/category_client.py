from typing import List, Any
from dataclasses import dataclass
from database.handlers.db_client import DBClient


@dataclass()
class CategoryClient(DBClient):
    def __init__(self, base_name: str = 'test_db'):
        super().__init__(base_name)

    def get_categories(self) -> list[str]:
        query = "select distinct category_name from category"
        cursor, conn = self._send_query(query)
        categories = cursor.fetchall()
        return [category[0] for category in categories]

    def get_category_by_name(self, name: str) -> int:
        query = f"select distinct category_id from category where category_name = '{name}'"
        cursor, conn = self._send_query(query)
        category_id = cursor.fetchone()
        conn.commit()
        conn.close()
        return int(category_id[0])

    def get_subcategories_id_by_name(self, category_id: int, subcategory_name: int) -> list[Any]:
        query = (f'''select category_id, subcategory_id from category 
                 where category_id = {category_id} and subcategory_name = '{subcategory_name}' ''')
        cursor, conn = self._send_query(query)
        categories_id = cursor.fetchone()
        conn.commit()
        conn.close()
        return [categories_id[0], categories_id[1]]

    def get_subcategories_by_category_id(self, category_id: int) -> list:
        query = f"select subcategory_name from category where category_id = {category_id}"
        cursor, conn = self._send_query(query)
        subcategories = cursor.fetchall()
        conn.commit()
        conn.close()
        return [subcat[0] for subcat in subcategories]

    def get_name_by_id(self, category_id: int, subcategory_id: int) -> list[Any]:
        query = f'''select category_name, subcategory_name from category
                    where category_id = {category_id} and subcategory_id = {subcategory_id}'''
        cursor, conn = self._send_query(query)
        names = cursor.fetchone()
        conn.commit()
        conn.close()
        return [names[0], names[1]]

    def get_id_by_tags(self, tags: list[str]) -> list[int]:
        tags_list = []
        for tag in tags:
            query = f'select id from tags where name = "{tag}"'
            if not self._check_exists(query):
                insert_query = f'insert into tags (name) values ("{tag}")'
                cursor, conn = self._send_query(insert_query)
                conn.commit()
                conn.close()
            cursor, conn = self._send_query(query)
            tags_list.append(cursor.fetchone()[0])
            conn.close()
        return tags_list

    def get_tags_by_id(self, ids: list[int]) -> list[str]:
        ids_list = ', '.join(ids)
        query = 'select name from tags where id in (' + ids_list + ')'
        cursor, conn = self._send_query(query)
        tags = cursor.fetchall()
        conn.close()
        return [tag[0] for tag in tags]
