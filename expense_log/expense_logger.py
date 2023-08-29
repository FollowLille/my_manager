import pandas as pd
from dataclasses import dataclass
from dateutil.parser import parse
from datetime import date, datetime, timedelta

COLUMNS = ['user', 'category', 'total_sum', 'report_date', 'tags']
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
        'replenishment': 'Пополнения',
    }

    def __init__(self):
        self.data = pd.read_csv(NAME, names=COLUMNS, index_col=False)

    def add_expense(self, expense: dict) -> None:
        self.__reopen_file()
        expense_ = {'user': expense.get('user'),
                    'category': expense.get('category'),
                    'total_sum': expense.get('total_sum'),
                    'report_date': expense.get('report_date'),
                    'tags': expense.get('tags')}
        df = pd.DataFrame([expense_])
        self.data = pd.concat([self.data, df], ignore_index=True)
        pd.DataFrame.to_csv(self.data, NAME, index=False, header=False)
        self.__reopen_file()

    def get_df(self, period: str) -> pd.DataFrame:
        df = pd.read_csv(NAME, names=COLUMNS)
        df['report_date'] = df['report_date'].apply(parse)
        df['category'] = df.category.apply(lambda x: self.category_dict.get(x))
        return self.__filter_df_by_period(df, period)[['user', 'category', 'total_sum']]

    @staticmethod
    def __filter_df_by_period(df: pd.DataFrame, period: str) -> pd.DataFrame:
        current_date = datetime.combine(date.today(), datetime.min.time())
        current_week = current_date.isocalendar()[1]
        current_month = datetime.now().month
        current_year = datetime.now().year
        df['week'] = df['report_date'].apply(lambda x: x.isocalendar()[1])
        df['month'] = df['report_date'].apply(lambda x: x.month)
        df['year'] = df['report_date'].apply(lambda x: x.year)
        if period == 'daily':
            df = df[df['report_date'] == current_date]
        elif period == 'weekly':
            df.query('week == @current_week and year == @current_year')
        elif period == 'monthly':
            df.query('month == @current_month and year == @current_year')
        elif period == 'yearly':
            df.query('year == @current_year')
        return df

    def __reopen_file(self) -> None:
        self.data = pd.read_csv(NAME, names=COLUMNS, index_col=False)
