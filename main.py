import pandas as pd
import numpy as np
import yaml
import telebot
from telebot import types
from users_configs.users_config import UsersLib


with open('secret.yml', 'r') as yml:
    token = yaml.safe_load(yml).get('token')
bot = telebot.TeleBot(token)
user_id = ''
chat_id = ''
known_users = UsersLib.get_users()


@bot.message_handler(commands=['start'])
def start(message):
    global user_id, chat_id
    chat_id = message.chat.id
    user_id = str(chat_id)
    if not known_users.get(user_id, False):
        message = bot.send_message(chat_id, 'Пользователь не найден, введите имя пользователя')
        bot.register_next_step_handler(message, user_reg)
    else:
        if known_users.get(user_id).lower() == 'котенька':
            bot.send_message(chat_id, 'Эта книга принадлежит самому лучшему человеку на свете!!!')
        print(f'{str(known_users[user_id])} has used app')


def user_reg(message):
    global known_users
    while message.text in known_users.values():
        message = bot.send_message(chat_id, 'Данное имя уже занято, попробуй другое')
    UsersLib.add_new_user(chat_id, message.text)
    print(f'Add new user with name {message.text}')
    known_users = UsersLib.get_users()


bot.infinity_polling(timeout=10, long_polling_timeout=5)