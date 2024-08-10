from utils.utils import *
import time


def activate_parser(bot, matches, users):
    all_matches = get_all_matches(matches)

    if len(all_matches) == 0:
        time.sleep(5)

    elif all_matches != 'error' and len(all_matches) != 0:
        users_list = get_users(users)

        for match in all_matches:
            file_of_match_page = save_page_source(match['link'], 'coefficients_parser')
            if file_of_match_page:
                new_coefficients = get_match_coefficients()
                if new_coefficients:
                    is_update = data_comparing(match, new_coefficients, matches)
                    if is_update:
                        for user in users_list:
                            bot.send_message(user['user'], is_update, disable_web_page_preview=True)
                else:
                    for user in users_list:
                        bot.send_message(user['user'], f'Матч {match["first_opponent"]} – {match["second_opponent"]} '
                                                       f'удален, т.к. матча уже не существует либо ставки на блоки '
                                                       f'исход/победа закрыты.')
                    matches.delete_one({'link': match['link']})
                    continue  # The match don't exist anymore.

            else:
                continue  # The error saving the page has arisen.

    elif all_matches == 'error':
        time.sleep(5)
