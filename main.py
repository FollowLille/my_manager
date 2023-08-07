import pandas as pd
import numpy as np
import datetime
import yaml
import re

import telebot
from telebot import types

from users_configs.users_config import UsersLib
from expense_log.expense_logger import ExpenseLogger

with open('secret.yml', 'r') as yml:
    token = yaml.safe_load(yml).get('token')
bot = telebot.TeleBot(token)
user_id = ''
chat_id = ''
known_users = UsersLib.get_users()
expenses_book = ExpenseLogger()


@bot.message_handler(commands=['start'])
def start(message):
    global user_id, chat_id
    chat_id = message.chat.id
    user_id = str(chat_id)
    if not known_users.get(user_id, False):
        message = bot.send_message(chat_id, 'Пользователь не найден, введите имя пользователя')
        bot.register_next_step_handler(message, user_reg)
    getting_started(message)


def user_reg(message):
    global known_users
    while message.text in known_users.values():
        message = bot.send_message(chat_id, 'Данное имя уже занято, попробуй другое')
    UsersLib.add_new_user(chat_id, message.text)
    print(f'Add new user with name {message.text}')
    known_users = UsersLib.get_users()
    getting_started()


def getting_started():
    rkm = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    rkm.add(types.KeyboardButton('Добавить расходы'), types.KeyboardButton('Вывести статистику'))
    bot.send_message(chat_id,
                     f'Привет, {str(known_users[user_id])}!\nЧто хочешь сделать дальше?', reply_markup=rkm,
                     allow_sending_without_reply=True)


@bot.message_handler(content_types=['text'])
def first_choice(message):
    global chat_id, user_id
    chat_id = message.chat.id
    user_id = str(chat_id)
    if message.text == 'Добавить расходы':
        add_expense()
    elif message.text == 'Вывести статистику':
        get_statistics()
    else:
        bot.send_message(chat_id, 'Неизвестная команда, возвращаю в главное меню')
        print(f'Unknown command, back to main menu')
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
        category = def_dic.partition('_')[0]
        exp_sum, _, exp_date = def_dic.partition('_')[2].partition('_')
        if not exp_date:
            get_date(category=category, exp_sum=exp_sum)
        add_expense_with_date(category=category, exp_sum=exp_sum, exp_date=exp_date)


def add_category(category: str):
    message = bot.send_message(chat_id, 'Введи сумму в формате 1999.99')
    bot.register_next_step_handler(message, add_date, category=category)


def add_date(message, category):
    ikm = types.InlineKeyboardMarkup(row_width=2)
    button1 = types.InlineKeyboardButton(
        'Оставить текущий день', callback_data=f'add_expense_with_date_{category}_{message.text}_{datetime.date.today()}')
    button2 = types.InlineKeyboardButton(
        'Ввести дату', callback_data=f'add_expense_with_date_{category}_{message.text}')
    ikm.add(button1, button2)
    bot.send_message(chat_id, 'Хотите ввести произвольную дату?', reply_markup=ikm)


def get_date(category: str, exp_sum: str):
    message = bot.send_message(chat_id, 'Введи дату в формате 1999-12-31')
    date_format = '[\d]{4}[.,-/][\d]{2}[.,-/][\d]{2}'
    if not re.fullmatch(date_format, message.text):
        message = bot.send_message(chat_id, 'Неправильный формат даты, введи заново')
        bot.register_next_step_handler(message, get_date, category=category, exp_sum=exp_sum)
    exp_date = message.text
    add_expense_with_date(category=category, exp_sum=exp_sum, exp_date=exp_date)


def add_expense_with_date(category, exp_sum, exp_date):
    expense = {'user': known_users.get(user_id), 'category': category, 'sum': exp_sum, 'report_date': exp_date}
    expenses_book.add_expense(expense)
    bot.send_message(chat_id, 'Покупка добавлена')
    getting_started()


def get_statistics():
    pass


bot.infinity_polling(timeout=10, long_polling_timeout=5)
