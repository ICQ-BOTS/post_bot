from bot.bot import Bot
from bot.handler import MessageHandler
from bot.filter import Filter

import config
import database
from event_handler import addbot_cm, main_message_main_bot, init_handler


def start_bots():
    bots = []
    for token in database.get_tokens():
        bot_token = Bot(token=token)
        print(token)
        if bot_token.self_get().json()['ok'] == True:
            bots.append(bot_token)
            print(token)
    for bot in bots:
        bot = init_handler(bot)
        bot.start_polling()


main_bot = Bot(token=config.MAIN_TOKEN)
main_bot.dispatcher.add_handler(MessageHandler(
    callback=addbot_cm,
    filters=Filter.regexp('(?i)^/addbot')
))
main_bot.dispatcher.add_handler(MessageHandler(
    callback=main_message_main_bot
))

main_bot.start_polling()
start_bots()
main_bot.idle()
