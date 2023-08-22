from datetime import date, timedelta
from dateutil.parser import parse
from keyboa import Keyboa, Button
import pandas as pd
import yaml

import telebot
from telebot import types

from users_configs.users_config import UsersLib
from expense_log.expense_logger import ExpenseLogger

with open('secret.yml', 'r') as yml:
    token = yaml.safe_load(yml).get('token')
bot = telebot.TeleBot(token)

user_id = ''
chat_id = ''
properties = {}
known_users = UsersLib.get_users()
expenses_book = ExpenseLogger()


@bot.message_handler(commands=['start'])
def start(message):
    global user_id, chat_id
    chat_id = message.chat.id
    user_id = str(chat_id)
    if not known_users.get(user_id, False).get('name'):
        message = bot.send_message(chat_id, 'Пользователь не найден, введите имя пользователя')
        bot.register_next_step_handler(message, user_reg)
    getting_started()


def user_reg(message):
    global known_users
    UsersLib.add_new_user(chat_id, message.text)
    print(f'Add new user with name {message.text}')
    known_users = UsersLib.get_users()
    getting_started()


def getting_started():
    rkm = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False, row_width=2)
    rkm.add(types.KeyboardButton('Добавить расходы'), types.KeyboardButton('Пополнения'),
            types.KeyboardButton('Вывести статистику'), types.KeyboardButton('Настройки'))
    bot.send_message(chat_id,
                     f'Привет, {str(known_users.get(user_id).get("name"))}!\nЧто хочешь сделать дальше?',
                     reply_markup=rkm, allow_sending_without_reply=True)


@bot.message_handler(content_types=['text'])
def first_choice(message):
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
        pass
    else:
        bot.send_message(chat_id, 'Неизвестная команда, возвращаю в главное меню')
        print(f'Unknown command {message.text}, back to main menu')
        getting_started()


def add_expense():
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


@bot.callback_query_handler(func=lambda call: True)
def callback_data(call):
    if 'add_category' in call.data:
        category = call.data.rpartition('_')[2]
        add_category(category)
    elif 'add_expense_with_date' in call.data:
        def_dic = call.data.replace('add_expense_with_date_', '')
        category, _, sum_date_tags_str = def_dic.partition('_')
        tags, _, sum_date_str = sum_date_tags_str.partition('_')
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
    elif 'mine' in call.data:
        change_vision_on_expenses(call.data.partition('_')[0])


def add_category(category: str):
    message = bot.send_message(chat_id, 'Введи сумму в формате 1999.99')
    bot.register_next_step_handler(message, add_sum, category=category)


def add_sum(message, category):
    cur_sum = message.text
    message = bot.send_message(chat_id, 'Добавьте теги (краткое описание, в одно слово)')
    bot.register_next_step_handler(message, add_date, category=category, cur_sum=cur_sum)


def add_date(message, category, cur_sum):
    ikm = types.InlineKeyboardMarkup(row_width=1)
    button1 = types.InlineKeyboardButton(
        'Оставить текущий день',
        callback_data=f'add_expense_with_date_{category}_{message.text}_{cur_sum}_{date.today()}')
    button2 = types.InlineKeyboardButton(
        'Выбрать вчерашний день',
        callback_data=f'add_expense_with_date_{category}_{message.text}_{cur_sum}_{date.today() - timedelta(days=1)}')
    button3 = types.InlineKeyboardButton(
        'Ввести дату', callback_data=f'add_expense_with_date_{category}_{message.text}_{cur_sum}')
    ikm.add(button1, button2, button3)
    bot.send_message(chat_id, 'Хотите ввести произвольную дату?', reply_markup=ikm)


def get_date(message, category: str, exp_sum: str, tags: str, user_message=None):
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


def add_expense_with_date(category: str, exp_sum: str, exp_date: str, tags: str):
    expense = {'user': user_id, 'category': category, 'sum': exp_sum, 'report_date': exp_date, 'tags': tags}
    expenses_book.add_expense(expense)
    rus_category = expenses_book.category_dict.get(category)
    cur_date = parse(exp_date).date().strftime('%d.%m.%Y')
    bot.send_message(
        chat_id,
        f'Добавлена трата за {cur_date} в категорию {rus_category} на сумму {exp_sum} с тэгом {tags}.')
    getting_started()


def get_statistics():
    ikm = types.InlineKeyboardMarkup(row_width=2)
    button1 = types.InlineKeyboardButton('Статистика за день', callback_data='get_df_daily')
    button2 = types.InlineKeyboardButton('Статистика за неделю', callback_data='get_df_weekly')
    button3 = types.InlineKeyboardButton('Статистика за месяц', callback_data='get_df_monthly')
    button4 = types.InlineKeyboardButton('Статистика за год', callback_data='get_df_yearly')
    ikm.add(button1, button2, button3, button4)
    message = bot.send_message(chat_id, 'Выбери период', reply_markup=ikm)
    # bot.delete_message(chat_id, message.id)


def get_df_by_period(period: str):
    df = expenses_book.get_df(period)
    if known_users.get(user_id).get('vision') == 'my':
        df = df[df['user'] == chat_id]
    print(df)
    if not df.empty:
        get_stats_by_df(df)
    else:
        bot.send_message(user_id, 'Данные за этот период отсутствуют')


def get_stats_by_df(df: pd.DataFrame):
    grouped_df = df.groupby('category').agg({'total_sum': 'sum', 'category': 'count'}).sort_values('total_sum',
                                                                                                   ascending=False)
    grouped_df = grouped_df[grouped_df['total_sum'] > 0]
    for category, value in grouped_df.iterrows():
        stats = f'{category} - {value.total_sum:.0f} р. ({value.category:.0f} шт.)'
        bot.send_message(user_id, stats)
    getting_started()


def get_properties():
    ikm = types.InlineKeyboardMarkup(row_width=2)
    button1 = types.InlineKeyboardButton('Изменить имя', callback_data='get_name')
    button2 = types.InlineKeyboardButton('Выводить только мои траты', callback_data='only_mine')
    button3 = types.InlineKeyboardButton('Выводить все траты', callback_data='not_only_mine')
    ikm.add(button1, button2, button3)
    bot.send_message(chat_id, 'Доступные команды', reply_markup=ikm)


def get_name():
    message = bot.send_message(chat_id, 'Введите новое имя: ')
    bot.register_next_step_handler(message, change_name)


def change_name(message):
    global known_users
    new_name = message.text
    UsersLib.change_name(chat_id, new_name)
    known_users = UsersLib.get_users()
    bot.send_message(chat_id, f'Имя успешно изменено на: {new_name}')
    getting_started()


def change_vision_on_expenses(rule: str):
    global known_users
    if rule == 'only':
        UsersLib.change_vision(chat_id, 'my')
        bot.send_message(chat_id, 'Теперь видны только твои траты')
    elif rule == 'not':
        UsersLib.change_vision(chat_id, 'all')
        bot.send_message(chat_id, 'Теперь видны все траты')
    known_users = UsersLib.get_users()
    getting_started()


def check_date(date_value: str):
    try:
        parse(date_value)
        return True
    except:
        print(f'unvalid date: {date_value}')
        return False


bot.infinity_polling(timeout=10, long_polling_timeout=5)
