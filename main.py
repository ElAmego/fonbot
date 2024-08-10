import telebot
from fonbot import activate_tg_bot
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

# Bot
bot = None  # The token from BotFather

# Database
url = None  # DB's url
client = MongoClient(url, server_api=ServerApi('1'))
db = client.fonbot_db
matches = db.matches
users = db.users


def main():
    activate_tg_bot(bot, matches, users)


if __name__ == '__main__':
    main()
