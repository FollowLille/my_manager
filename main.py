from datetime import date, timedelta
from dateutil.parser import parse
from keyboa import Keyboa, Button
import pandas as pd
import json
import yaml

import telebot
from telebot import types

from users_configs.users_config import UsersLib
from expense_log.expense_logger import ExpenseLogger
from expenses_dict.replace_dict import ReplaceDict
from database.database_handler import UserClient

with open('secret.yml', 'r') as yml:
    token = yaml.safe_load(yml).get('token')
bot = telebot.TeleBot(token)


category_path = 'my_manager/expenses_dict/category'
tags_path = 'my_manager/expenses_dict/tags'
known_users = UsersLib.get_users()
expenses_book = ExpenseLogger()
replacer = ReplaceDict()
with open('my_manager/expenses_dict/category.json') as file:
    category_dict = json.load(file)


@bot.message_handler(commands=['start'])
def start(message: types.Message):
    try:
        if not known_users.get(str(message.chat.id), False).get('name'):
            message = bot.send_message(message.chat.id, 'Пользователь не найден, введите имя пользователя')
            bot.register_next_step_handler(message, user_reg)
        user_name = known_users.get(str(message.chat.id), False).get('name')
        bot.send_message(message.chat.id, f'Привет, {user_name}')
        getting_started(message)
    except Exception as exc:
        print(exc)
        bot.send_message(message.chat.id, 'Непонятная ошибка, попробуй заново')
        getting_started(message)


def user_reg(message: types.Message):
    try:
        global known_users
        UsersLib.add_new_user(message.chat.id, message.text)
        print(f'Add new user with name {message.text}')
        known_users = UsersLib.get_users()
        getting_started(message)
    except Exception as exc:
        print(exc)
        bot.send_message(message.chat.id, 'Непонятная ошибка, попробуй заново')
        getting_started(message)


def getting_started(message: types.Message):
    try:
        rkm = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False, row_width=2)
        rkm.add(types.KeyboardButton('Добавить расходы'), types.KeyboardButton('Пополнения'),
                types.KeyboardButton('Вывести статистику'), types.KeyboardButton('Настройки'))
        bot.send_message(message.chat.id, f'Что хочешь сделать дальше?',
                         reply_markup=rkm, allow_sending_without_reply=True)
    except Exception as exc:
        print(exc)
        bot.send_message(message.chat.id, 'Непонятная ошибка, попробуй заново')
        getting_started(message)


@bot.message_handler(content_types=['text'])
def first_choice(message: types.Message):
    try:
        if message.text == 'Добавить расходы':
            add_category(message=message)
        elif message.text == 'Вывести статистику':
            get_statistics(message=message)
        elif message.text == 'Настройки':
            get_properties(message=message)
        elif message.text == 'Пополнения':
            add_sum(message=message, category='p', sub_category='p')
        else:
            bot.send_message(message.chat.id, 'Неизвестная команда, возвращаю в главное меню')
            print(f'Unknown command {message.text}, back to main menu')
            getting_started(message)
    except Exception as exc:
        print(exc)
        bot.send_message(message.chat.id, 'Непонятная ошибка, попробуй заново')
        getting_started(message)


def add_category(message: types.Message):
    try:
        ikm = types.InlineKeyboardMarkup(row_width=2)
        button_list = []
        for category in category_dict:
            button = types.InlineKeyboardButton(category, callback_data=f'add_category_{category}')
            button_list.append(button)
        ikm.add(*button_list)
        bot.send_message(message.chat.id, 'Выбери категорию', reply_markup=ikm)
    except Exception as exc:
        print(exc)
        bot.send_message(message.chat.id, 'Непонятная ошибка, попробуй заново')
        getting_started(message)


@bot.callback_query_handler(func=lambda call: True)
def callback_data(call):
    try:
        if 'add_category' in call.data:
            category = call.data.rsplit('_')[2]
            convert_category = replacer.convert(category, category_path)
            add_sub_categories(message=call.message, category=convert_category)
        if 'add_subcategory' in call.data:
            category, subcategory = call.data.split('_')[2:]
            add_sum(call.message, category, subcategory)
        elif 'add_expense_with_date' in call.data:
            def_dic = call.data.replace('add_expense_with_date_', '')
            category, sub_category, tags_str, exp_sum, exp_date = def_dic.split('_')
            if category != 'p':
                category, sub_category = replacer.reverse_convert_subcategories(category, sub_category, category_path)
            else:
                category, sub_category = 'Пополнения', 'Пополнения'
            tags_str = tags_str.replace('[', '').replace(']', '').lower()
            tags_list = [tag.strip() for tag in tags_str.split(',')]
            tags = replacer.reverse_list_convert(tags_list, tags_path)
            if not exp_date:
                get_date(message=call.message, category=category, sub_category=sub_category, exp_sum=exp_sum, tags=tags)
            else:
                add_expense_with_date(message=call.message, category=category, sub_category=sub_category,
                                      exp_sum=exp_sum, exp_date=exp_date, tags=tags)
        elif 'get_df' in call.data:
            period = call.data.rpartition('_')[2]
            get_df_by_period(message=call.message, period=period)
        elif 'get_name' in call.data:
            get_name(message=call.message)
        elif 'stats' in call.data:
            change_vision_on_expenses(message=call.message, rule=call.data.partition('_')[0])
        elif 'group' in call.data:
            group_managment(message=call.data)
    except Exception as exc:
        print(exc)
        bot.send_message(call.message.chat.id, 'Непонятная ошибка, попробуй заново')
        getting_started(call.message)


def add_sub_categories(message: types.Message, category: str):
    try:
        subcategories = category_dict.get(replacer.get_key_by_value(category, category_path))
        ikm = types.InlineKeyboardMarkup(row_width=2)
        button_list = []
        for sub_cat in subcategories.get('sub_categories'):
            category = replacer.get_key_by_value(category, category_path)
            category, sub_category = replacer.convert_subcategories(category, sub_cat, category_path)
            button = types.InlineKeyboardButton(text=sub_cat,
                                                callback_data=f'add_subcategory_{category}_{sub_category}')
            button_list.append(button)
        ikm.add(*button_list)
        bot.send_message(message.chat.id, 'Выбери подкатегорию', reply_markup=ikm)
    except Exception as exc:
        print(exc)
        bot.send_message(message.chat.id, 'Непонятная ошибка, попробуй заново')
        getting_started(message)


def add_sum(message: types.Message, category: str, sub_category: str):
    try:
        message = bot.send_message(message.chat.id, 'Введи сумму в формате 1999.99')
        bot.register_next_step_handler(message, add_tags, category=category, sub_category=sub_category)
    except Exception as exc:
        print(exc)
        bot.send_message(message.chat.id, 'Непонятная ошибка, попробуй заново')
        getting_started(message)


def add_tags(message: types.Message, category: str, sub_category: str):
    try:
        cur_sum = float(message.text)
        message = bot.send_message(message.chat.id, 'Добавьте теги (по одному слову, через запятую)')
        bot.register_next_step_handler(message, add_date, category=category, sub_category=sub_category, cur_sum=cur_sum)
    except (TypeError, ValueError) as exc:
        print(f'Невозможно перевести переменную "{message.text}" в формат float')
        bot.send_message(message.chat.id, 'Неверный формат суммы, попробуй заново')
        getting_started(message=message)
    except Exception as exc:
        print(exc)
        bot.send_message(message.chat.id, 'Непонятная ошибка, попробуй заново')
        getting_started(message)


def add_date(message: types.Message, category: str, sub_category: str, cur_sum: float):
    try:
        ikm = types.InlineKeyboardMarkup(row_width=1)
        tags = message.text.split(',')
        tags_list = [tag.strip().lower() for tag in tags]
        converted_tags = replacer.list_convert(tags_list, tags_path)
        button1 = types.InlineKeyboardButton(
            'Оставить текущий день',
            callback_data=f'add_expense_with_date_{category}_{sub_category}_{converted_tags}_{cur_sum}_{date.today()}')
        button2 = types.InlineKeyboardButton(
            'Выбрать вчерашний день',
            callback_data=f'add_expense_with_date_{category}_{sub_category}_{converted_tags}_{cur_sum}_{date.today() - timedelta(days=1)}')
        button3 = types.InlineKeyboardButton(
            'Ввести дату', callback_data=f'add_expense_with_date_{category}_{sub_category}_{converted_tags}_{cur_sum}_')
        ikm.add(button1, button2, button3)
        bot.send_message(message.chat.id, 'Выбери дату', reply_markup=ikm)
    except Exception as exc:
        print(exc)
        bot.send_message(message.chat.id, 'Непонятная ошибка, попробуй заново')
        getting_started(message)


def get_date(message: types.Message, category: str, sub_category: str, exp_sum: str, tags: list,
             user_message: bool = None, is_not_first: bool = None):
    try:
        if not user_message:
            message = bot.send_message(message.chat.id, 'Введи дату в формате 1999-12-31')
            bot.register_next_step_handler(message, get_date, category=category, sub_category=sub_category,
                                           exp_sum=exp_sum, tags=tags, user_message=True, is_not_first=False)
        else:
            if not check_date(message.text):
                if not is_not_first:
                    message = bot.send_message(message.chat.id,
                                               text='Неправильный формат даты, введи заново\nИспользуй только цифры и символы\nДля отмены введи любую букву\nИли нажми любую кнопку :)''')
                    bot.register_next_step_handler(message, get_date, category=category, sub_category=sub_category,
                                                   exp_sum=exp_sum, tags=tags, user_message=True, is_not_first=True)
                else:
                    if message.text.replace(' ','').isalpha():
                        getting_started(message)
                    else:
                        message = bot.send_message(message.chat.id,
                                                   text='Неправильный формат даты, введи заново\nИспользуй только цифры и символы\nДля отмены введи любую букву\nИли нажми любую кнопку :)''')
                        bot.register_next_step_handler(message, get_date, category=category, sub_category=sub_category,
                                                       exp_sum=exp_sum, tags=tags, user_message=True, is_not_first=True)

            else:
                exp_date = message.text
                add_expense_with_date(message=message, category=category, sub_category=sub_category, exp_sum=exp_sum,
                                      exp_date=exp_date, tags=tags)
    except Exception as exc:
        print(exc)
        bot.send_message(message.chat.id, 'Непонятная ошибка, попробуй заново')
        getting_started(message)


def add_expense_with_date(message: types.Message, category: str, sub_category: str, exp_sum: str, exp_date: str,
                          tags: list):
    try:
        expense = {'user': str(message.chat.id), 'category': category, 'sub_category': sub_category, 'total_sum': exp_sum,
                   'report_date': exp_date, 'tags': tags}
        expenses_book.add_expense(expense)
        cur_date = parse(exp_date).date().strftime('%d.%m.%Y')
        print(f'add new rows: {expense}')
        if category == 'Пополнения':
            bot.send_message(message.chat.id, f'Добавлено пополнение за {cur_date} на сумму {exp_sum} с тэгом {tags}')
        else:
            bot.send_message(message.chat.id,
                             f'Добавлена трата за {cur_date} в категорию {category}/{sub_category} на сумму {exp_sum} с тегом {tags}.')

        getting_started(message)
    except Exception as exc:
        print(exc)
        bot.send_message(message.chat.id, 'Непонятная ошибка, попробуй заново')
        getting_started(message)


def get_statistics(message: types.Message):
    try:
        ikm = types.InlineKeyboardMarkup(row_width=2)
        button1 = types.InlineKeyboardButton('Статистика за день', callback_data='get_df_daily')
        button2 = types.InlineKeyboardButton('Статистика за неделю', callback_data='get_df_weekly')
        button3 = types.InlineKeyboardButton('Статистика за месяц', callback_data='get_df_monthly')
        button4 = types.InlineKeyboardButton('Статистика за год', callback_data='get_df_yearly')
        ikm.add(button1, button2, button3, button4)
        bot.send_message(message.chat.id, 'Выбери период', reply_markup=ikm)
    except Exception as exc:
        print(exc)
        bot.send_message(message.chat.id, 'Непонятная ошибка, попробуй заново')
        getting_started(message)


def get_df_by_period(message: types.Message, period: str):
    try:
        df = expenses_book.get_df(period)
        if known_users.get(str(message.chat.id)).get('vision') == 'my':
            df = df[df['user'] == message.chat.id]
        if not df.empty:
            get_stats_by_df(message, df)
        else:
            bot.send_message(message.chat.id, 'Данные за этот период отсутствуют')
    except Exception as exc:
        print(exc)
        bot.send_message(message.chat.id, 'Непонятная ошибка, попробуй заново')
        getting_started(message)


def get_stats_by_df(message: types.Message, df: pd.DataFrame):
    try:
        grouped_df = df.groupby('category').agg({'total_sum': 'sum', 'category': 'count'}).sort_values('total_sum',
                                                                                                       ascending=False)
        grouped_df = grouped_df[grouped_df['total_sum'] > 0]
        stats = 'Траты: \n'
        for category, value in grouped_df.iterrows():
            if category == 'Пополнения':
                continue
            else:
                stats += f'{category} - {value.total_sum:.0f} р. ({value.category:.0f} шт.)\n'
        repl_df = grouped_df.loc[grouped_df.index == 'Пополнения']
        stats += '\nПополнения:\n'
        for category, value in repl_df.iterrows():
            stats += f'{value.total_sum:.0f} р. ({value.category:.0f} шт.)\n'
        bot.send_message(message.chat.id, stats)
        getting_started(message)
    except Exception as exc:
        print(exc)
        bot.send_message(message.chat.id, 'Непонятная ошибка, попробуй заново')
        getting_started(message)


def get_properties(message: types.Message):
    try:
        ikm = types.InlineKeyboardMarkup(row_width=2)
        button1 = types.InlineKeyboardButton('Изменить имя', callback_data='get_name')
        button2 = types.InlineKeyboardButton('Выводить только мои траты', callback_data='only_mine_stats')
        button3 = types.InlineKeyboardButton('Выводить все траты', callback_data='not_only_mine_stats')
        button4 = types.InlineKeyboardButton('Создать группу', callback_data='create_group')
        button5 = types.InlineKeyboardButton('Добавить группу', callback_data='add_group')
        button6 = types.InlineKeyboardButton('Удалить группу', callback_data='delete_group')
        ikm.add(button1, button2, button3, button4, button5, button6)
        bot.send_message(message.chat.id, 'Доступные команды', reply_markup=ikm)
    except Exception as exc:
        print(exc)
        bot.send_message(message.chat.id, 'Непонятная ошибка, попробуй заново')
        getting_started(message)


def get_name(message: types.Message):
    try:
        message = bot.send_message(message.chat.id, 'Введите новое имя: ')
        bot.register_next_step_handler(message, change_name)
    except Exception as exc:
        print(exc)
        bot.send_message(message.chat.id, 'Непонятная ошибка, попробуй заново')
        getting_started(message)


def change_name(message):
    try:
        new_name = message.text
        UsersLib.change_name(message.chat.id, new_name)
        known_users = UsersLib.get_users()
        bot.send_message(message.chat.id, f'Имя успешно изменено на: {new_name}')
        getting_started(message)
    except Exception as exc:
        print(exc)
        bot.send_message(message.chat.id, 'Непонятная ошибка, попробуй заново')
        getting_started(message)


def change_vision_on_expenses(message: types.Message, rule: str):
    try:
        global known_users
        if rule == 'only':
            UsersLib.change_vision(message.chat.id, 'my')
            bot.send_message(message.chat.id, 'Теперь видны только твои траты')
        elif rule == 'not':
            UsersLib.change_vision(message.chat.id, 'all')
            bot.send_message(message.chat.id, 'Теперь видны все траты')
        known_users = UsersLib.get_users()
        getting_started(message)
    except Exception as exc:
        print(exc)
        bot.send_message(message.chat.id, 'Непонятная ошибка, попробуй заново')
        getting_started(message)


def group_management(message: types.Message):
    chat_id = message.chat.id
    if 'create' in message:
        check_count_of_group(message)
        message = bot.send_message(chat_id, 'Придумай название для группы')
    elif 'add' in message:
        pass
    elif 'delete' in message:
        pass


def check_count_of_group(message: types.Message) -> int:
    pass


def check_date(date_value: str):
    try:
        parse(date_value)
        return True
    except:
        print(f'unvalid date: {date_value}')
        return False

def group_managment(message):
    pass

bot.infinity_polling(timeout=10, long_polling_timeout=5)
