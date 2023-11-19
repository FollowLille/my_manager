from datetime import date, timedelta, datetime
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta
import pandas as pd
import locale
import yaml

import telebot
from telebot import types
from keyboa import Keyboa, Button
from polog import log, config, file_writer

from database.database_handler import UserClient, ExpenseClient, LimitClient, CategoryClient, GroupClient

with open('./secret.yml', 'r') as yml:
    token = yaml.safe_load(yml).get('token')
bot = telebot.TeleBot(token)

config.add_handlers(file_writer('main_log'))

path_to_db = 'my_manager/database/main_base'
user_client = UserClient(path_to_db)
expenses_book = ExpenseClient(path_to_db)
limit_client = LimitClient(path_to_db)
category_client = CategoryClient(path_to_db)
category_dict = category_client.get_categories()
group_client = GroupClient(path_to_db)
locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')


@log
@bot.message_handler(commands=['start'])
def start(message: types.Message):
    try:
        user_name = user_client.get_user(message.chat.id)
        if not user_name:
            message = bot.send_message(message.chat.id, 'Пользователь не найден, введите имя пользователя')
            bot.register_next_step_handler(message, user_reg)
        else:
            bot.send_message(message.chat.id, f'Привет, {user_name}')
            getting_started(message)
    except Exception as exc:
        bot.send_message(message.chat.id, 'Непонятная ошибка, попробуй заново')
        getting_started(message)


@log
def user_reg(message: types.Message):
    try:
        user_client.add_user(message.chat.id, message.text)
        bot.send_message(message.chat.id, f'Добавлен новый пользователь с именем {message.text}')
        getting_started(message)
    except Exception as exc:
        bot.send_message(message.chat.id, 'Непонятная ошибка, попробуй заново')
        getting_started(message)


@log
def getting_started(message: types.Message):
    try:
        rkm = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False, row_width=2)
        rkm.add(types.KeyboardButton('Добавить расходы'), types.KeyboardButton('Пополнения'),
                types.KeyboardButton('Вывести статистику'), types.KeyboardButton('Лимиты'),
                types.KeyboardButton('Настройки'))
        bot.send_message(message.chat.id, f'Что хочешь сделать дальше?',
                         reply_markup=rkm, allow_sending_without_reply=True)
    except Exception as exc:
        bot.send_message(message.chat.id, 'Непонятная ошибка, попробуй заново')
        getting_started(message)


@log
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
        elif message.text == 'Лимиты':
            limit_handler(message=message)
        else:
            bot.send_message(message.chat.id, 'Неизвестная команда, возвращаю в главное меню')
            getting_started(message)
    except Exception as exc:
        bot.send_message(message.chat.id, 'Непонятная ошибка, попробуй заново')
        getting_started(message)


@log
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
        bot.send_message(message.chat.id, 'Непонятная ошибка, попробуй заново')
        getting_started(message)


@log
@bot.callback_query_handler(func=lambda call: 'add_category' in call.data)
def add_category_callback(call):
    try:
        category = call.data.rsplit('_')[2]
        category_id = category_client.get_category_by_name(category)
        add_sub_categories(message=call.message, category=category_id)
    except Exception as exc:
        bot.send_message(call.message.chat.id, 'Непонятная ошибка, попробуй заново')
        getting_started(call.message)


@log
def add_sub_categories(message: types.Message, category: int):
    try:
        subcategories = category_client.get_subcategories_by_category_id(category)
        ikm = types.InlineKeyboardMarkup(row_width=2)
        button_list = []
        for sub_cat in subcategories:
            category, sub_category = category_client.get_subcategories_id_by_name(category, sub_cat)
            button = types.InlineKeyboardButton(text=sub_cat,
                                                callback_data=f'add_subcategory_{category}_{sub_category}')
            button_list.append(button)
        ikm.add(*button_list)
        bot.send_message(message.chat.id, 'Выбери подкатегорию', reply_markup=ikm)
    except Exception as exc:
        bot.send_message(message.chat.id, 'Непонятная ошибка, попробуй заново')
        getting_started(message)


@log
@bot.callback_query_handler(func=lambda call: 'add_subcategory' in call.data)
def add_subcategory_callback(call):
    try:
        category, subcategory = call.data.split('_')[2:]
        add_sum(call.message, category, subcategory)
    except Exception as exc:
        bot.send_message(call.message.chat.id, 'Непонятная ошибка, попробуй заново')
        getting_started(call.message)


@log
def add_sum(message: types.Message, category: str, sub_category: str):
    try:
        message = bot.send_message(message.chat.id, 'Введи сумму в формате 1999.99')
        bot.register_next_step_handler(message, add_tags, category=category, sub_category=sub_category)
    except Exception as exc:
        bot.send_message(message.chat.id, 'Непонятная ошибка, попробуй заново')
        getting_started(message)


@log
def add_tags(message: types.Message, category: str, sub_category: str):
    try:
        cur_sum = float(message.text)
        message = bot.send_message(message.chat.id, 'Добавьте теги (по одному слову, через запятую)')
        bot.register_next_step_handler(message, add_date, category=category, sub_category=sub_category, cur_sum=cur_sum)
    except (TypeError, ValueError) as exc:
        bot.send_message(message.chat.id, 'Неверный формат суммы, попробуй заново')
        getting_started(message=message)
    except Exception as exc:
        bot.send_message(message.chat.id, 'Непонятная ошибка, попробуй заново')
        getting_started(message)


@log
def add_date(message: types.Message, category: str, sub_category: str, cur_sum: float):
    try:
        ikm = types.InlineKeyboardMarkup(row_width=1)
        tags = message.text.split(',')
        tags_list = [tag.strip().lower() for tag in tags]
        converted_tags = category_client.get_id_by_tags(tags_list)
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
        bot.send_message(message.chat.id, 'Непонятная ошибка, попробуй заново')
        getting_started(message)


@log
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
                                               text='Неправильный формат даты, введи заново\nИспользуй только цифры и'
                                                    'символы\nДля отмены введи любую букву\nИли нажми любую кнопку '
                                                    ':)''')
                    bot.register_next_step_handler(message, get_date, category=category, sub_category=sub_category,
                                                   exp_sum=exp_sum, tags=tags, user_message=True, is_not_first=True)
                else:
                    if message.text.replace(' ', '').isalpha():
                        getting_started(message)
                    else:
                        message = bot.send_message(message.chat.id,
                                                   text='Неправильный формат даты, введи заново\nИспользуй только'
                                                        'цифры и символы\nДля отмены введи любую букву\nИли нажми '
                                                        'любую кнопку :)''')
                        bot.register_next_step_handler(message, get_date, category=category, sub_category=sub_category,
                                                       exp_sum=exp_sum, tags=tags, user_message=True, is_not_first=True)

            else:
                exp_date = message.text
                add_expense_with_date(message=message, category=category, sub_category=sub_category, exp_sum=exp_sum,
                                      exp_date=exp_date, tags=tags)
    except Exception as exc:
        bot.send_message(message.chat.id, 'Непонятная ошибка, попробуй заново')
        getting_started(message)


@log
def add_expense_with_date(message: types.Message, category: str, sub_category: str, exp_sum: str, exp_date: str,
                          tags: list):
    try:
        expense = {'user_id': str(message.chat.id), 'category': category, 'subcategory': sub_category,
                   'expenses_sum': exp_sum,
                   'report_date': exp_date, 'tags': tags}
        expenses_book.add_expense(expense)
        cur_date = parse(exp_date).date().strftime('%d.%m.%Y')
        if category == 'Пополнения':
            bot.send_message(message.chat.id, f'Добавлено пополнение за {cur_date} на сумму {exp_sum} с тэгом {tags}')
        else:
            bot.send_message(message.chat.id,
                             f'Добавлена трата за {cur_date} в категорию {category}/{sub_category} на сумму {exp_sum} с тегом {tags}.')

        getting_started(message)
    except Exception as exc:
        bot.send_message(message.chat.id, 'Непонятная ошибка, попробуй заново')
        getting_started(message)


@log
@bot.callback_query_handler(func=lambda call: 'add_expense_with_date' in call.data)
def add_expense_callback(call):
    try:
        def_dic = call.data.replace('add_expense_with_date_', '')
        category, sub_category, tags_str, exp_sum, exp_date = def_dic.split('_')
        if category != 'p':
            category, sub_category = category_client.get_name_by_id(category, sub_category)
        else:
            category, sub_category = 'Пополнения', 'Пополнения'
        tags_str = tags_str.replace('[', '').replace(']', '').lower()
        tags_list = [tag.strip() for tag in tags_str.split(',')]
        tags = category_client.get_tags_by_id(tags_list)
        if not exp_date:
            get_date(message=call.message, category=category, sub_category=sub_category, exp_sum=exp_sum, tags=tags)
        else:
            add_expense_with_date(message=call.message, category=category, sub_category=sub_category,
                                  exp_sum=exp_sum, exp_date=exp_date, tags=tags)
    except Exception as exc:
        bot.send_message(call.message.chat.id, 'Непонятная ошибка, попробуй заново')
        getting_started(call.message)


@log
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
        bot.send_message(message.chat.id, 'Непонятная ошибка, попробуй заново')
        getting_started(message)


@log
@bot.callback_query_handler(func=lambda call: 'get_df' in call.data)
def add_statistics_callback(call):
    try:
        period = call.data.rpartition('_')[2]
        get_df_by_period(message=call.message, period=period)
    except Exception as exc:
        bot.send_message(call.message.chat.id, 'Непонятная ошибка, попробуй заново')
        getting_started(call.message)


@log
def get_df_by_period(message: types.Message, period: str, interval: str = '0', id_to_edit: int = None):
    try:
        df = expenses_book.get_statistics(period, interval)
        if user_client.get_user(message.chat.id, vision=True) == 'my':
            df = df[df['user_id'] == message.chat.id]
        get_stats_by_df(message, df, period, interval, id_to_edit)
    except Exception as exc:
        bot.send_message(message.chat.id, 'Непонятная ошибка, попробуй заново')
        getting_started(message)


@log
def get_stats_by_df(message: types.Message, df: pd.DataFrame, period: str, interval: str = '0', id_to_edit: int = None):
    try:
        # Только траты
        cur_period = get_cur_period(period, interval)
        total_msg = f'{cur_period}\n\n'
        exp_df = df.loc[df.category != 'Пополнения']
        total_sum, total_cnt = exp_df.total_sum.sum(), exp_df.total_count.sum()
        total_msg += f'Итого:\nСумма - {total_sum}  р.\nКоличество - {total_cnt} шт.\n\n'
        stats = 'Траты: \n'
        for index, value in exp_df.iterrows():
            stats += f'{value.category} - {value.total_sum:.0f} р. ({value.total_count:} шт.)\n'
        # Пополнения
        repl_df = df.loc[df.category == 'Пополнения']
        stats += '\nПополнения:\n'
        for index, value in repl_df.iterrows():
            stats += f'{value.total_sum:.0f} р. ({value.total_count:.0f} шт.)\n'

        previous_period = {'⏪️': f'previous_button_{period}_{interval}'}
        next_period = {'⏩️': f'next_button_{period}_{interval}'}
        keyboard = Keyboa(items=[previous_period, next_period], items_in_row=2)
        if not id_to_edit:
            message = bot.send_message(message.chat.id, total_msg + stats, reply_markup=keyboard())
            getting_started(message)
        else:
            message = bot.edit_message_text(total_msg + stats, message.chat.id, id_to_edit, reply_markup=keyboard())
    except Exception as exc:
        bot.send_message(message.chat.id, 'Непонятная ошибка, попробуй заново')
        getting_started(message)


@log
@bot.callback_query_handler(func=lambda call: 'next_button' in call.data or 'previous_button' in call.data)
def get_df_with_new_period(call):
    try:
        *_, period, interval = call.data.split('_')
        message_id = call.message.id
        interval = int(interval)
        if 'next' in call.data:
            interval += 1
        if 'previous' in call.data:
            interval += -1
        get_df_by_period(call.message, period, str(interval), id_to_edit=message_id)
    except Exception as exc:
        bot.send_message(call.message.chat.id, 'Непонятная ошибка, попробуй заново')
        getting_started(call.message)


@log
def limit_handler(message: types.Message):
    try:
        ikm = types.InlineKeyboardMarkup()
        button1 = types.InlineKeyboardButton('Мои лимиты', callback_data='my_limits')
        button2 = types.InlineKeyboardButton('Добавить лимит', callback_data='add_limits')
        button3 = types.InlineKeyboardButton('Удалить лимит', callback_data='delete_limits')
        button4 = types.InlineKeyboardButton('Статистика', callback_data='view_on_limits')
        ikm.add(button1, button2, button3, button4)
        bot.send_message(message.chat.id, 'Список доступных действий', reply_markup=ikm)
    except Exception as exc:
        bot.send_message(message.chat.id, 'Непонятная ошибка, попробуй заново')
        getting_started(message)


@log
@bot.callback_query_handler(func=lambda call: 'limits' in call.data)
def limit_callback(call):
    try:
        if 'add' in call.data:
            ikm = types.InlineKeyboardMarkup(row_width=2)
            button_list = []
            for category in category_dict:
                button = types.InlineKeyboardButton(category, callback_data=f'add_limit_category_{category}')
                button_list.append(button)
            ikm.add(*button_list)
            bot.send_message(call.message.chat.id, 'Выбери категорию', reply_markup=ikm)
        elif 'my' in call.data:
            df = limit_client.get_limits(call.message.chat.id)
            stats = 'Текущие лимиты\n'
            for index, value in df.iterrows():
                stats += f'{value.category}: {value.cat_limit}\n'
            mes_id = call.message.chat.id
            bot.send_message(call.message.chat.id, stats)
            getting_started(call.message)
        elif 'delete' in call.data:
            df = limit_client.get_limits(call.message.chat.id)
            if df.empty:
                bot.send_message(call.message.chat.id, 'У вас нет лимитов')
            else:
                ikm = types.InlineKeyboardMarkup(row_width=2)
                button_list = []
                for category in df.category:
                    button = types.InlineKeyboardButton(category, callback_data=f'delete_limit_category_{category}')
                    button_list.append(button)
                ikm.add(*button_list)
                bot.send_message(call.message.chat.id, 'Выбери категорию', reply_markup=ikm)
        elif 'view_on' in call.data:
            limits = limit_client.get_limits(call.message.chat.id)
            expenses = expenses_book.get_statistics('monthly')
            merged_df = pd.merge(limits, expenses, how='left', on='category').fillna(0)
            merged_df['limit_sum'] = merged_df['cat_limit'] - merged_df['total_sum']
            stats = 'Итого:\n'
            for index, value in merged_df.iterrows():
                stats += f'''{value.category}:\n\tЛимит: {value.cat_limit}\n\tТраты: {value.total_sum}\n\tОстаток: {value.limit_sum}\n'''
            bot.send_message(call.message.chat.id, stats)
            getting_started(call.message)
    except Exception as exc:
        bot.send_message(call.message, 'Непонятная ошибка, попробуй заново')
        getting_started(call.message)


@log
@bot.callback_query_handler(func=lambda call: 'add_limit_category' in call.data)
def add_limits(call):
    try:
        category = call.data.rpartition('_')[2]
        message = bot.send_message(call.message.chat.id, 'Введи сумму')
        bot.register_next_step_handler(message, add_limit_to_db, category=category)
    except Exception as exc:
        bot.send_message(call.message.chat.id, 'Непонятная ошибка, попробуй заново')
        getting_started(call.message)


@log
def add_limit_to_db(message, category: str):
    try:
        limit = int(message.text)
        if limit_client.add_limit(message.chat.id, category, limit) != 'success':
            bot.send_message(message.chat.id, 'Лимит в данной категории уже заведен')
            message = bot.send_message(message.chat.id,
                                       'Изменить текущие лимиты или посмотреть их можно через раздел Лимиты')
        else:
            message = bot.send_message(message.chat.id, f'Успешно введен лимит в категории {category} на сумму {limit}')
        getting_started(message)
    except Exception as exc:
        bot.send_message(message.chat.id, 'Непонятная ошибка, попробуй заново')
        getting_started(message)


@log
@bot.callback_query_handler(func=lambda call: 'delete_limit_category' in call.data)
def delete_limit(call):
    try:
        category = call.data.rpartition('_')[2]
        limit_client.delete_limit(call.message.chat.id, category)
        bot.send_message(call.message.chat.id, f'Лимит в категории {category} успешно удален')
        getting_started(call.message)
    except Exception as exc:
        bot.send_message(call.message.chat.id, 'Непонятная ошибка, попробуй заново')
        getting_started(call.message)


@log
def get_properties(message: types.Message):
    try:
        ikm = types.InlineKeyboardMarkup(row_width=2)
        button1 = types.InlineKeyboardButton('Изменить имя', callback_data='get_name')
        button2 = types.InlineKeyboardButton('Выводить только мои траты', callback_data='only_mine_stats')
        button3 = types.InlineKeyboardButton('Выводить все траты моей группы', callback_data='not_only_mine_stats')
        button4 = types.InlineKeyboardButton('Управление группами', callback_data='group_management')
        ikm.add(button1, button2, button3, button4)
        bot.send_message(message.chat.id, 'Доступные команды', reply_markup=ikm)
    except Exception as exc:
        bot.send_message(message.chat.id, 'Непонятная ошибка, попробуй заново')
        getting_started(message)


@log
@bot.callback_query_handler(func=lambda call: 'group_management' in call.data)
def add_category_callback(call):
    try:
        message = '''Для создания группы с другим пользователем нужно: 
        1. Передать другому пользователю свой уникальный номер
        2. Другой пользователь должен открыть раздел "Управление группами" > "Добавить пользователя" и ввести там ваш номер
        3. Другой пользователь должен передать вам свой номер и вы должны повторить п.2
        Возможность выводить свои траты или траты группы можно в меню "Настройки" '''
        bot.send_message(call.message.chat.id, message)
        bot.send_message(call.message.chat.id, f'Ваш уникальный номер: @{call.message.chat.id}')
        ikm = types.InlineKeyboardMarkup(row_width=1)
        button1 = types.InlineKeyboardButton('Добавить пользователя в группу', callback_data='users_group_add')
        button2 = types.InlineKeyboardButton('Удалить пользователя из группы', callback_data='users_group_delete')
        ikm.add(button1, button2)
        bot.send_message(call.message.chat.id, 'Выбери действие:', reply_markup=ikm)
    except Exception as exc:
        bot.send_message(call.message.chat.id, 'Непонятная ошибка, попробуй заново')
        getting_started(call.message)


@log
@bot.callback_query_handler(func=lambda call: 'users_group' in call.data)
def change_users_group(call):
    message = call.message
    try:
        message = bot.send_message(message.chat.id, 'Введи номер пользователя, которого хотите добавить или удалить')
        if 'add' in call.data:
            bot.register_next_step_handler(message, add_user)
        elif 'delete' in call.data:
            bot.register_next_step_handler(message, delete_user)
    except Exception as exc:
        bot.send_message(message.chat.id, 'Непонятная ошибка, попробуй заново')
        getting_started(message)


@log
def delete_user(message: types.Message):
    try:
        id_to_delete = message.text.replace('@', '')
        user_id = message.chat.id
        answer = group_client.delete_user(int(user_id), int(id_to_delete))
        bot.send_message(message.chat.id, answer)
        getting_started(message)
    except Exception as exc:
        bot.send_message(message.chat.id, 'Непонятная ошибка, попробуй заново')
        getting_started(message)


@log
def add_user(message: types.Message):
    try:
        id_to_add = message.text.replace('@', '')
        user_id = message.chat.id
        answer = group_client.add_user(int(user_id), int(id_to_add))
        bot.send_message(message.chat.id, answer)
        getting_started(message)
    except Exception as exc:
        bot.send_message(message.chat.id, 'Непонятная ошибка, попробуй заново')
        getting_started(message)


@log
@bot.callback_query_handler(func=lambda call: 'get_name' in call.data or 'mine_stats' in call.data)
def add_category_callback(call):
    try:
        if 'get_name' in call.data:
            get_name(call.message)
        elif 'mine_stats' in call.data:
            change_vision_on_expenses(message=call.message, rule=call.data.partition('_')[0])
    except Exception as exc:
        bot.send_message(call.message.chat.id, 'Непонятная ошибка, попробуй заново')
        getting_started(call.message)


@log
def get_name(message: types.Message):
    try:
        message = bot.send_message(message.chat.id, 'Введите новое имя: ')
        bot.register_next_step_handler(message, change_name)
    except Exception as exc:
        bot.send_message(message.chat.id, 'Непонятная ошибка, попробуй заново')
        getting_started(message)


@log
def change_name(message):
    try:
        user_client.change_user_info(user_id=message.chat.id, user_name=message.text)
        bot.send_message(message.chat.id, f'Имя успешно изменено на: {message.text}')
        getting_started(message)
    except Exception as exc:
        bot.send_message(message.chat.id, 'Непонятная ошибка, попробуй заново')
        getting_started(message)


@log
def change_vision_on_expenses(message: types.Message, rule: str):
    try:
        if rule == 'only':
            user_client.change_user_info(user_id=message.chat.id, vision='my')
            bot.send_message(message.chat.id, 'Теперь видны только твои траты')
        elif rule == 'not':
            user_client.change_user_info(user_id=message.chat.id, vision='all')
            bot.send_message(message.chat.id, 'Теперь видны все траты')
        getting_started(message)
    except Exception as exc:
        bot.send_message(message.chat.id, 'Непонятная ошибка, попробуй заново')
        getting_started(message)


@log
def check_date(date_value: str):
    try:
        parse(date_value)
        return True
    except:
        return False


@log
def get_cur_period(period, interval):
    cur_date = date.today()
    interval = int(interval)
    if period == 'daily':
        cur_date = cur_date + timedelta(days=interval)
        cur_date = datetime.strftime(cur_date, '%d %B %Y')
    elif period == 'weekly':
        cur_date = cur_date + timedelta(days=interval * 7)
        weekday = cur_date.isoweekday() - 1
        if weekday == -1:
            weekday = 7
        week_start = cur_date - timedelta(days=weekday % 7)
        week_end = week_start + timedelta(days=6)
        rus_week_start = datetime.strftime(week_start, '%d %B %Y')
        rus_week_end = datetime.strftime(week_end, '%d %B %Y')
        cur_date = f'{rus_week_start} - {rus_week_end}'
    elif period == 'monthly':
        cur_date += relativedelta(months=interval)
        cur_date = datetime.strftime(cur_date, '%B %Y')
    elif period == 'yearly':
        cur_date += relativedelta(years=interval)
        cur_date = datetime.strftime(cur_date, '%Y')
    return str(cur_date)


print('Started')
bot.infinity_polling(timeout=10, long_polling_timeout=5)
