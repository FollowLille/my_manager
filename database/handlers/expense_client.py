import pandas as pd
from dataclasses import dataclass
from database.handlers.db_client import DBClient


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

    def get_statistics(self, period: str = 'monthly', interval: str = None) -> pd.DataFrame:
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
