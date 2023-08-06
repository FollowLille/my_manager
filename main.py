import pandas as pd
import numpy as np
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
    button1 = types.InlineKeyboardButton('Продукты', callback_data=add_category)
    button2 = types.InlineKeyboardButton('Развлечения')
    button3 = types.InlineKeyboardButton('Рестораны')
    button4 = types.InlineKeyboardButton('Аптеки')
    button5 = types.InlineKeyboardButton('Одежда')
    button6 = types.InlineKeyboardButton('Дом')
    button7 = types.InlineKeyboardButton('Транспорт')
    button8 = types.InlineKeyboardButton('Прочее')
    ikm.add(button1, button2, button3, button4, button5, button6, button7, button8)
    bot.send_message(chat_id, 'Выбери категорию', reply_markup=ikm)


def add_category():
    print(message.text)

def get_statistics():
    pass

bot.infinity_polling(timeout=10, long_polling_timeout=5)