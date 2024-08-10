from selenium import webdriver
from bs4 import BeautifulSoup
import time


def save_page_source(url: str, location: str) -> bool:
    driver = webdriver.Firefox()
    try:
        driver.get(url)
        time.sleep(8)

        if location == 'tg_bot':
            with open('page.html', 'w', encoding='utf-8') as file:
                file.write(driver.page_source)
        elif location == 'coefficients_parser':
            with open('page_for_parser.html', 'w', encoding='utf-8') as file:
                file.write(driver.page_source)

    except Exception as ex:
        print(f'The error in the save_page_source function: {ex}')
        return False

    else:
        return True

    finally:
        driver.close()
        driver.quit()


def get_data_match() -> dict | bool:
    coefficients = None
    try:
        with open('page.html', 'r', encoding='utf-8') as file:
            src = file.read()
            soup = BeautifulSoup(src, 'lxml')
        opponents = soup.find_all(class_=['scoreboard-compact__main__team__name--wEKOc', 'scoreboard__table__team__name'
                                                                                         '--A6TDN'])

        for block in soup.find_all('div', class_=['text--NI31Y']):
            if block.text == 'Победа в матче' or block.text == 'Исход' or block.text == 'Итоговая победа':
                coefficients = soup.find_all('div', class_=['value--v77pD'])[:2]
                break

            elif block.text == 'Исход матча (основное время)' or block.text == 'Исход матча':
                coefficients = soup.find_all('div', class_=['value--v77pD'])[:3]
                break

    except AttributeError as ex:
        print(f'The error in the get_data_match function: {ex}')
        return False

    else:
        if coefficients:
            match_data = {
                'opponents': [opponent.text for opponent in opponents],
                'coefficients': [float(coefficient.text) for coefficient in coefficients]
            }
            return match_data

        else:
            return False


def add_match_into_the_db(match_data: dict, link: str, matches) -> bool:
    data = {
        'first_opponent': match_data['opponents'][0],
        'second_opponent': match_data['opponents'][1],
        'link': link,
        'coefficients': match_data['coefficients']
    }

    try:
        matches.insert_one(data)

    except Exception as ex:
        print(f'The error in the add_match_into_the_db function: {ex}')
        return False

    else:
        return True


def delete_match_from_the_db(all_matches: list or None, nums: str, matches) -> bool:
    if ',' in nums:
        nums = nums.split(', ')
    elif nums.lower() == 'все':
        nums = 'all'
    else:
        nums = list(nums)

    try:
        if nums != 'all':
            for num in nums:
                matches.delete_one({'link': all_matches[int(num)-1]['link']})

        else:
            matches.delete_many({})

    except Exception and IndexError and ValueError as ex:
        print(f'The error in the delete_match_from_the_db function: {ex}')
        return False
    else:
        return True


def checking_match_in_the_db(link: str, matches) -> str | bool:
    try:
        res = matches.find_one({'link': f'{link}'})
    except Exception as ex:
        print(f'The error in the checking_match_in_the_db function: {ex}')
        return False

    else:
        return 'already_was' if res else True


def get_all_matches(matches) -> list | bool:
    try:
        all_matches = list(matches.find().sort({'_id': -1}))
    except Exception as ex:
        print(f'The error in the get_all_matches function: {ex}')
        return False
    else:
        return all_matches


def make_message_of_matches(all_matches: list) -> str:
    msg = 'Список отслеживаемых матчей:\n'

    for index, match in enumerate(all_matches):
        msg += f'{index+1}: {match["first_opponent"]} – {match["second_opponent"]}\nСсылка на матч:  {match["link"]}\n'
        if len(match['coefficients']) == 2:
            msg += (f'Коэффициенты: Победа {match["first_opponent"]}: {match["coefficients"][0]}, '
                    f'Победа {match["second_opponent"]}: {match["coefficients"][1]}\n')
        else:
            msg += (f'Коэффициенты: Победа {match["first_opponent"]}: {match["coefficients"][0]},'
                    f' Ничья: {match["coefficients"][1]}, Победа {match["second_opponent"]}: '
                    f'{match["coefficients"][2]}\n')

    return msg


def get_match_coefficients() -> list | bool:
    divs_with_coefficients = None

    try:
        with open('page_for_parser.html', 'r', encoding='utf-8') as file:
            src = file.read()
        soup = BeautifulSoup(src, 'lxml')

        for block in soup.find_all('div', class_=['text--NI31Y']):
            if block.text == 'Победа в матче' or block.text == 'Исход' or block.text == 'Итоговая победа':
                divs_with_coefficients = soup.find_all('div', class_=['value--v77pD'])[:2]
                break

            elif block.text == 'Исход матча (основное время)' or block.text == 'Исход матча':
                divs_with_coefficients = soup.find_all('div', class_=['value--v77pD'])[:3]
                break

    except AttributeError as ex:
        print(f'The error in the get_match_coefficients function: {ex}')
        return False

    else:
        if divs_with_coefficients:
            coefficients = [float(coefficient.text) for coefficient in divs_with_coefficients]

            return coefficients
        else:
            return False


def data_comparing(match: dict, new_coefficients: list, matches) -> str | bool:
    if match['coefficients'] == new_coefficients:
        return False  # New coefficients match with the preceding coefficients.
    else:
        msg = (f'В матче {match["first_opponent"]} – {match["second_opponent"]} изменились коэффициент(ы): \n'
               f'Ссылка на матч: {match["link"]} \n')
        if len(new_coefficients) == 3:
            for index, value in enumerate(new_coefficients):
                if value not in match['coefficients']:
                    match index:
                        case 0:
                            msg += (f'Коэффициент на победу {match["first_opponent"]} '
                                    f'{"увеличился" if value > match["coefficients"][index] else "упал"} с '
                                    f'{match["coefficients"][index]} на {value}\n')

                        case 1:
                            msg += (f'Коэффициент на ничью '
                                    f'{"увеличился" if value > match["coefficients"][index] else "упал"} с '
                                    f'{match["coefficients"][index]} на {value}\n')

                        case 2:
                            msg += (f'Коэффициент на победу {match["second_opponent"]} '
                                    f'{"увеличился" if value > match["coefficients"][index] else "упал"} с '
                                    f'{match["coefficients"][index]} на {value}\n')
        else:
            for index, value in enumerate(new_coefficients):
                if value not in match['coefficients']:
                    match index:
                        case 0:
                            msg += (f'Коэффициент на победу {match["first_opponent"]} '
                                    f'{"увеличился" if value > match["coefficients"][index] else "упал"} с '
                                    f'{match["coefficients"][index]} на {value}\n')

                        case 1:
                            msg += (f'Коэффициент на победу {match["second_opponent"]} '
                                    f'{"увеличился" if value > match["coefficients"][index] else "упал"} с '
                                    f'{match["coefficients"][index]} на {value}\n')
    try:
        matches.update_one({'link': match['link']}, {'$set': {'coefficients': new_coefficients}})
    except Exception as ex:
        print(f'The error in the data_comparing function: {ex}')
        return False
    else:
        return msg


def check_user(users, user):
    try:
        is_exist = list(users.find({'user': user}))

        if len(is_exist) == 0:
            users.insert_one({'user': user})

    except Exception as ex:
        print(f'The error in the check_user function: {ex}')


def get_users(users) -> list | bool:
    try:
        users_list = list(users.find({}, {'user': -1}))
        return users_list
    except Exception as ex:
        print(f'The error in the get_users function: {ex}')
        return False
