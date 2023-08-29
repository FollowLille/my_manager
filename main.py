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

with open('secret.yml', 'r') as yml:
    token = yaml.safe_load(yml).get('token')
bot = telebot.TeleBot(token)

user_id = ''
chat_id = ''
category_path = 'my_manager/expenses_dict/category'
tags_path = 'my_manager/expenses_dict/tags'
properties = {}
known_users = UsersLib.get_users()
expenses_book = ExpenseLogger()
replacer = ReplaceDict()


@bot.message_handler(commands=['start'])
def start(message):
    try:
        global user_id, chat_id
        chat_id = message.chat.id
        user_id = str(chat_id)
        if not known_users.get(user_id, False).get('name'):
            message = bot.send_message(chat_id, 'Пользователь не найден, введите имя пользователя')
            bot.register_next_step_handler(message, user_reg)
        getting_started()
    except Exception as exc:
        print(exc)
        bot.send_message(chat_id, 'Непонятная ошибка, попробуй заново')
        getting_started()


def user_reg(message):
    try:
        global known_users
        UsersLib.add_new_user(chat_id, message.text)
        print(f'Add new user with name {message.text}')
        known_users = UsersLib.get_users()
        getting_started()
    except Exception as exc:
        print(exc)
        bot.send_message(chat_id, 'Непонятная ошибка, попробуй заново')
        getting_started()


def getting_started():
    try:
        rkm = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False, row_width=2)
        rkm.add(types.KeyboardButton('Добавить расходы'), types.KeyboardButton('Пополнения'),
                types.KeyboardButton('Вывести статистику'), types.KeyboardButton('Настройки'))
        bot.send_message(chat_id,
                         f'Привет, {str(known_users.get(user_id).get("name"))}!\nЧто хочешь сделать дальше?',
                         reply_markup=rkm, allow_sending_without_reply=True)
    except Exception as exc:
        print(exc)
        bot.send_message(chat_id, 'Непонятная ошибка, попробуй заново')
        getting_started()


@bot.message_handler(content_types=['text'])
def first_choice(message):
    try:
        global chat_id, user_id
        chat_id = message.chat.id
        user_id = str(chat_id)
        if message.text == 'Добавить расходы':
            add_expense()
        elif message.text == 'Вывести статистику':
            get_statistics()
        elif message.text == 'Настройки':
            get_properties()
        elif message.text == 'Пополнения':
            add_category(replacer.get_value_by_key('replenishment', category_path))
        else:
            bot.send_message(chat_id, 'Неизвестная команда, возвращаю в главное меню')
            print(f'Unknown command {message.text}, back to main menu')
            getting_started()
    except Exception as exc:
        print(exc)
        bot.send_message(chat_id, 'Непонятная ошибка, попробуй заново')
        getting_started()


def add_expense():
    try:
        ikm = types.InlineKeyboardMarkup(row_width=2)
        button1 = types.InlineKeyboardButton('Продукты', callback_data='add_category_products')
        button2 = types.InlineKeyboardButton('Развлечения', callback_data='add_category_entertainments')
        button3 = types.InlineKeyboardButton('Рестораны', callback_data='add_category_restaurant')
        button4 = types.InlineKeyboardButton('Аптеки', callback_data='add_category_pharmacy')
        button5 = types.InlineKeyboardButton('Одежда', callback_data='add_category_clothes')
        button6 = types.InlineKeyboardButton('Дом', callback_data='add_category_home')
        button7 = types.InlineKeyboardButton('Транспорт', callback_data='add_category_transport')
        button8 = types.InlineKeyboardButton('Прочее', callback_data='add_category_other')
        ikm.add(button1, button2, button3, button4, button5, button6, button7, button8)
        bot.send_message(chat_id, 'Выбери категорию', reply_markup=ikm)
    except Exception as exc:
        print(exc)
        bot.send_message(chat_id, 'Непонятная ошибка, попробуй заново')
        getting_started()


@bot.callback_query_handler(func=lambda call: True)
def callback_data(call):
    try:
        if 'add_category' in call.data:
            category = call.data.rpartition('_')[2]
            convert_category = replacer.convert(category, category_path)
            add_category(convert_category)
        elif 'add_expense_with_date' in call.data:
            print(call.data)
            def_dic = call.data.replace('add_expense_with_date_', '')
            category_int, _, sum_date_tags_str = def_dic.partition('_')
            category = replacer.revers_convert(category_int, category_path)
            tags_str, _, sum_date_str = sum_date_tags_str.partition('_')
            tags_str = tags_str.replace('[', '').replace(']', '')
            tags_list = [tag.strip() for tag in tags_str.split(',')]
            tags = replacer.revers_list_convert(tags_list, tags_path)
            exp_sum, _, exp_date = sum_date_str.partition('_')
            if not exp_date:
                get_date(message=None, category=category, exp_sum=exp_sum, tags=tags)
            else:
                add_expense_with_date(category=category, exp_sum=exp_sum, exp_date=exp_date, tags=tags)
        elif 'get_df' in call.data:
            period = call.data.rpartition('_')[2]
            get_df_by_period(period=period)
        elif 'get_name' in call.data:
            get_name()
        elif 'mine_stats' in call.data:
            change_vision_on_expenses(call.data.partition('_')[0])
    except Exception as exc:
        print(exc)
        bot.send_message(chat_id, 'Непонятная ошибка, попробуй заново')
        getting_started()


def add_category(category: str):
    try:
        message = bot.send_message(chat_id, 'Введи сумму в формате 1999.99')
        bot.register_next_step_handler(message, add_sum, category=category)
    except Exception as exc:
        print(exc)
        bot.send_message(chat_id, 'Непонятная ошибка, попробуй заново')
        getting_started()


def add_sum(message, category):
    try:
        cur_sum = message.text
        message = bot.send_message(chat_id, 'Добавьте теги (по одному слову, через запятую)')
        bot.register_next_step_handler(message, add_date, category=category, cur_sum=cur_sum)
    except Exception as exc:
        print(exc)
        bot.send_message(chat_id, 'Непонятная ошибка, попробуй заново')
        getting_started()


def add_date(message, category, cur_sum):
    try:
        ikm = types.InlineKeyboardMarkup(row_width=1)
        tags = message.text.split(',')
        tags_list = [tag.strip() for tag in tags]
        converted_tags = replacer.list_convert(tags_list, tags_path)
        button1 = types.InlineKeyboardButton(
            'Оставить текущий день',
            callback_data=f'add_expense_with_date_{category}_{converted_tags}_{cur_sum}_{date.today()}')
        button2 = types.InlineKeyboardButton(
            'Выбрать вчерашний день',
            callback_data=f'add_expense_with_date_{category}_{converted_tags}_{cur_sum}_{date.today() - timedelta(days=1)}')
        button3 = types.InlineKeyboardButton(
            'Ввести дату', callback_data=f'add_expense_with_date_{category}_{converted_tags}_{cur_sum}')
        ikm.add(button1, button2, button3)
        bot.send_message(chat_id, 'Выбери дату', reply_markup=ikm)
    except Exception as exc:
        print(exc)
        bot.send_message(chat_id, 'Непонятная ошибка, попробуй заново')
        getting_started()


def get_date(message, category: str, exp_sum: str, tags: str, user_message=None):
    try:
        if not user_message:
            message = bot.send_message(chat_id, 'Введи дату в формате 1999-12-31')
            bot.register_next_step_handler(message, get_date, category=category, exp_sum=exp_sum, tags=tags,
                                           user_message=True)
        else:
            if not check_date(message.text):
                message = bot.send_message(chat_id, 'Неправильный формат даты, введи заново')
                bot.register_next_step_handler(message, get_date, category=category, exp_sum=exp_sum, tags=tags,
                                               user_message=True)
            else:
                exp_date = message.text
                add_expense_with_date(category=category, exp_sum=exp_sum, exp_date=exp_date, tags=tags)
    except Exception as exc:
        print(exc)
        bot.send_message(chat_id, 'Непонятная ошибка, попробуй заново')
        getting_started()


def add_expense_with_date(category: str, exp_sum: str, exp_date: str, tags: str):
    try:
        expense = {'user': user_id, 'category': category, 'total_sum': exp_sum, 'report_date': exp_date, 'tags': tags}
        expenses_book.add_expense(expense)
        rus_category = expenses_book.category_dict.get(category)
        cur_date = parse(exp_date).date().strftime('%d.%m.%Y')
        print(f'add new rows: {expense}')
        if category == 'replenishment':
            bot.send_message(chat_id, f'Добавлено пополнение за {cur_date} на сумму {exp_sum} с тэгом {tags}')
        else:
            bot.send_message(chat_id,
                             f'Добавлена трата за {cur_date} в категорию {rus_category} на сумму {exp_sum} с тегом {tags}.')

        getting_started()
    except Exception as exc:
        print(exc)
        bot.send_message(chat_id, 'Непонятная ошибка, попробуй заново')
        getting_started()


def get_statistics():
    try:
        ikm = types.InlineKeyboardMarkup(row_width=2)
        button1 = types.InlineKeyboardButton('Статистика за день', callback_data='get_df_daily')
        button2 = types.InlineKeyboardButton('Статистика за неделю', callback_data='get_df_weekly')
        button3 = types.InlineKeyboardButton('Статистика за месяц', callback_data='get_df_monthly')
        button4 = types.InlineKeyboardButton('Статистика за год', callback_data='get_df_yearly')
        ikm.add(button1, button2, button3, button4)
        bot.send_message(chat_id, 'Выбери период', reply_markup=ikm)
    except Exception as exc:
        print(exc)
        bot.send_message(chat_id, 'Непонятная ошибка, попробуй заново')
        getting_started()


def get_df_by_period(period: str):
    try:
        df = expenses_book.get_df(period)
        if known_users.get(user_id).get('vision') == 'my':
            df = df[df['user'] == chat_id]
        if not df.empty:
            get_stats_by_df(df)
        else:
            bot.send_message(user_id, 'Данные за этот период отсутствуют')
    except Exception as exc:
        print(exc)
        bot.send_message(chat_id, 'Непонятная ошибка, попробуй заново')
        getting_started()


def get_stats_by_df(df: pd.DataFrame):
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
        bot.send_message(user_id, stats)
        getting_started()
    except Exception as exc:
        print(exc)
        bot.send_message(chat_id, 'Непонятная ошибка, попробуй заново')
        getting_started()


def get_properties():
    try:
        ikm = types.InlineKeyboardMarkup(row_width=2)
        button1 = types.InlineKeyboardButton('Изменить имя', callback_data='get_name')
        button2 = types.InlineKeyboardButton('Выводить только мои траты', callback_data='only_mine_stats')
        button3 = types.InlineKeyboardButton('Выводить все траты', callback_data='not_only_mine_stats')
        ikm.add(button1, button2, button3)
        bot.send_message(chat_id, 'Доступные команды', reply_markup=ikm)
    except Exception as exc:
        print(exc)
        bot.send_message(chat_id, 'Непонятная ошибка, попробуй заново')
        getting_started()


def get_name():
    try:
        message = bot.send_message(chat_id, 'Введите новое имя: ')
        bot.register_next_step_handler(message, change_name)
    except Exception as exc:
        print(exc)
        bot.send_message(chat_id, 'Непонятная ошибка, попробуй заново')
        getting_started()



def change_name(message):
    try:
        global known_users
        new_name = message.text
        UsersLib.change_name(chat_id, new_name)
        known_users = UsersLib.get_users()
        bot.send_message(chat_id, f'Имя успешно изменено на: {new_name}')
        getting_started()
    except Exception as exc:
        print(exc)
        bot.send_message(chat_id, 'Непонятная ошибка, попробуй заново')
        getting_started()



def change_vision_on_expenses(rule: str):
    try:
        global known_users
        if rule == 'only':
            UsersLib.change_vision(chat_id, 'my')
            bot.send_message(chat_id, 'Теперь видны только твои траты')
        elif rule == 'not':
            UsersLib.change_vision(chat_id, 'all')
            bot.send_message(chat_id, 'Теперь видны все траты')
        known_users = UsersLib.get_users()
        getting_started()
    except Exception as exc:
        print(exc)
        bot.send_message(chat_id, 'Непонятная ошибка, попробуй заново')
        getting_started()



def check_date(date_value: str):
    try:
        parse(date_value)
        return True
    except:
        print(f'unvalid date: {date_value}')
        return False


bot.infinity_polling(timeout=10, long_polling_timeout=5)
