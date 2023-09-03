import sqlite3 as sq
from dataclasses import dataclass
from database_handler import DBClient, UserClient, ExpenseClient
import datetime
expenses = {"user_id": 213213,
            "category": "Продукты",
            "subcategory": "Прочее",
            "cur_sum": 300.01,
            "tags": (', ').join([tag for tag in ['самокат, доставка']]),
            "report_date": datetime.date.today() - datetime.timedelta(days=2)}

client = ExpenseClient()
client.add_expense(expenses)
print(client.get_expenses())



