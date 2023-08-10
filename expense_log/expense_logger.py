import pandas as pd
from dataclasses import dataclass
from dateutil.parser import parse

COLUMNS = ['user', 'category', 'sum', 'report_date']
NAME = 'my_manager/expense_log/expenses.csv'
pd.options.mode.chained_assignment = None


@dataclass
class ExpenseLogger:
    category_dict = {
        'other': 'Прочее',
        'transport': 'Транспорт',
        'home': 'Дом',
        'clothes': 'Одежда',
        'pharmacy': 'Аптеки',
        'restaurant': 'Рестораны',
        'entertainments': 'Развлечения',
        'products': 'Продукты',
    }

    def __init__(self):
        self.data = pd.read_csv(NAME, names=COLUMNS, index_col=False)

    def add_expense(self, expense: dict) -> None:
        self.__reopen_file()
        expense_ = {'user': expense.get('user'),
                    'category': expense.get('category'),
                    'sum': expense.get('sum'),
                    'report_date': expense.get('report_date')}
        df = pd.DataFrame([expense_])
        self.data = self.data.append(df)
        pd.DataFrame.to_csv(self.data, NAME, index=False, header=False)
        self.__reopen_file()

    def get_df(self):
        df = pd.read_csv(NAME, names=COLUMNS)
        df['report_date'] = df['report_date'].apply(parse)
        print(df)

    def __reopen_file(self) -> None:
        self.data = pd.read_csv(NAME, names=COLUMNS)
