from utils.utils import *
from telebot import types
from threading import Thread
from parser import activate_parser

all_matches = None


def activate_tg_bot(bot, matches, users):
    @bot.message_handler(commands=['start'])
    def start(message):
        check_user(users, message.chat.id)
        bot.send_message(message.chat.id, f'Добро пожаловать '
                                          f'{message.from_user.first_name} {message.from_user.last_name}!')

    @bot.message_handler(commands=['commands'])
    def commands(message):
        bot.send_message(message.chat.id, 'Список всех команд FonBot\n/add_match – Добавить матч.\n'
                                          '/list_match – Список отслеживаемых матчей.\n/commands – Список всех команд.')

    @bot.message_handler(commands=['add_match'])
    def add_match(message):
        bot.send_message(message.chat.id,
                         'Введите ссылку на игру (например: https://fonbet.by/sports/football/20330/48378970).',
                         disable_web_page_preview=True)
        bot.register_next_step_handler(message, add_link)

    @bot.message_handler(commands=['list_match'])
    def list_match(message):
        global all_matches
        all_matches = get_all_matches(matches)
        markup = types.InlineKeyboardMarkup()

        if len(all_matches) >= 0:
            if len(all_matches) != 0:
                markup.add(types.InlineKeyboardButton('Перестать отслеживать матч(и)?', callback_data='delete_match'))
                msg = make_message_of_matches(all_matches)

                bot.send_message(message.chat.id, msg, reply_markup=markup, disable_web_page_preview=True)
            else:
                bot.send_message(message.chat.id, 'Список отслеживаемых матчей пуст.')
        else:
            bot.send_message(message.chat.id, 'Ошибка при получении данных из базы данных.')

    @bot.callback_query_handler(func=lambda callback: True)
    def callback_message(callback):
        if callback.data == 'add_one_more':
            msg = bot.send_message(callback.from_user.id,
                                   'Введите ссылку на матч (например: https://fonbet.by/sports/football/20330/48378970)'
                                   '.', disable_web_page_preview=True)
            bot.register_next_step_handler(msg, add_link)

        if callback.data == 'delete_match':
            msg = bot.send_message(callback.from_user.id, 'Введите номер(а) матчей через запятую или "все".')
            bot.register_next_step_handler(msg, delete_match)

    def add_link(message):
        bot.send_message(message.chat.id, 'Матч добавляется, ожидайте.')
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('Добавить ещё одну игру?', callback_data='add_one_more'))
        is_check = checking_match_in_the_db(message.text, matches)

        if is_check and is_check != 'already_was':
            is_save = save_page_source(message.text, 'tg_bot')

            if is_save:
                data_match = get_data_match()

                if data_match:
                    is_add = add_match_into_the_db(data_match, message.text, matches)
                    if is_add:
                        bot.send_message(message.chat.id,
                                         f'Матч {data_match["opponents"][0]} – {data_match["opponents"][1]} '
                                         f'добавлен.', reply_markup=markup)

                    else:
                        bot.send_message(message.chat.id, 'Ошибка при добавлении данных в базу данных.',
                                         reply_markup=markup)

                else:
                    bot.send_message(message.chat.id, 'При анализе страницы произошла ошибка, возможно вы ввели ссылку '
                                                      'некорректно.', reply_markup=markup)

            else:
                bot.send_message(message.chat.id, 'Возникла ошибка при записи содержимого страницы.',
                                 reply_markup=markup)

        elif is_check == 'already_was':
            bot.send_message(message.chat.id, 'Матч уже отслеживается.', reply_markup=markup)
        else:
            bot.send_message(message.chat.id, 'Ошибка при получении данных из базы данных.', reply_markup=markup)

    def delete_match(message):
        is_delete = delete_match_from_the_db(all_matches, message.text, matches)
        if is_delete:
            bot.send_message(message.chat.id, 'Матч(и) больше не отслеживаются.')
        else:
            bot.send_message(message.chat.id,
                             'При удалении записи произошла ошибка, возможно вы ввели номер(а) не корректно.')

    def polling():
        bot.polling(none_stop=True)

    def parser():
        activate_parser(bot, matches, users)
        parser()

    polling_thread = Thread(target=polling)
    parser_thread = Thread(target=parser)
    polling_thread.start()
    parser_thread.start()
