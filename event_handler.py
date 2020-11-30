import json
import re

from bot.bot import Bot
from bot.handler import BotButtonCommandHandler, MessageHandler, DefaultHandler
from bot.filter import Filter

import database

       

def init_user_bot(func):
    def wrapper(*args, **kwargs):
        kwargs['user_info'] = database.check_user(kwargs['event'].data["from"]["userId"],kwargs['bot'].token)
        if kwargs['user_info']["not_exist"]:
            database.add_user(kwargs['event'].data["from"]["userId"],kwargs['event'].data["from"]["firstName"],kwargs['event'].data["from"]["lastName"])
            kwargs['user_info'] = database.check_user(kwargs['event'].data["from"]["userId"],kwargs['bot'].token)
        func(*args, **kwargs)
    return wrapper


def init_user(func):
    def wrapper(*args, **kwargs):
        kwargs['user_info'] = database.check_user(kwargs['event'].data["from"]["userId"])
        if kwargs['user_info']["not_exist"]:
            name = kwargs['event'].data["from"].get("firstName", " ")
            lastname = kwargs['event'].data["from"].get("lastName", " ")
            database.add_user(kwargs['event'].data["from"]["userId"], name, lastname)
            kwargs['user_info'] = database.check_user(kwargs['event'].data["from"]["userId"])
        func(*args, **kwargs)
    return wrapper


def init_handler(bot):
    bot.dispatcher.add_handler(MessageHandler(
        callback=admin_cm,
        filters=Filter.regexp(r'(?i)^/admin')
    ))
    bot.dispatcher.add_handler(MessageHandler(
        callback=noadmin_cm,
        filters=Filter.regexp(r'(?i)^/noadmin')
    ))
    bot.dispatcher.add_handler(MessageHandler(
        callback=setpublic_cm,
        filters=Filter.regexp(r'(?i)^/setpublic')
    ))
    bot.dispatcher.add_handler(MessageHandler(
        callback=myid_cm,
        filters=Filter.regexp(r'(?i)^/myid')
    ))
    bot.dispatcher.add_handler(DefaultHandler(
        callback=default_cm
    ))
    bot.dispatcher.add_handler(
        BotButtonCommandHandler(callback=button_processing
    ))
    return bot


@init_user
def addbot_cm(bot, event, user_info=None):
    if len(event.data["text"]) > 8:
        text = event.data["text"][8:]
        add_new_bot(bot, event.data, text)
    else:
        message = "Ты забыл прислать данные бота :)"
        bot.send_text(chat_id=event.data["chat"]["chatId"], text=message)
        main_message_main_bot(bot, event.data)



def add_new_bot(bot, data, text):
    text_arr = text.split("\n")
    for text in text_arr:
        if re.match(r'token:', text):
            new_token = text[7:]
            public_info = database.check_public(new_token)
            if public_info["not_exist"]:
                seq_key = database.add_bot(new_token)
                text1 = """Твой бот готов к работе!

                Новые команды доступные в тоем боте:
                /setpublic *Ключ доступа* *id паблика* - Установаить чат для этого бота
                id паблика можно найти в конце ссылки вашего чата https://icq.im/*********
                /unread - Получить необработанные публикации (только для администратора)
                /admin *Ключ доступа* *id пользователя* - Добавить администратора
                /noadmin *Ключ доступа* *id пользователя* - Удалить администратора
                /myid - Получить свой id (нужен для добавления и удаления администраторов)"""
                bot.send_text(chat_id=data["chat"]["chatId"], text=text1)
                text2 = "Твой ключ безопасности для твоего бота " + \
                    str(seq_key) + "\nЗапомни его!"
                bot.send_text(chat_id=data["chat"]["chatId"], text=text2)
                new_bot = Bot(token=new_token)
                if new_bot.self_get().json()['ok'] == True:
                    new_bot = init_handler(new_bot)
                    new_bot.dispatcher.add_handler(
                        BotButtonCommandHandler(callback=button_processing))
                    new_bot.start_polling()
            else:
                text = "Данный бот уже добавлен!"
                bot.send_text(chat_id=data["chat"]["chatId"], text=text)


@init_user
def main_message_main_bot(bot, event, user_info=None):
    text = """Я создатель ботов для администрирования новых публикаций!

    Чтобы создать и подключить нового бота:
    1) Напиши @metabot: /newbot - Чтобы создать нового бота
    2) Дай имя своему боту, которое должно заканчиваться на bot
    3) Смотри внимательнее, чтобы имя не было занято
    4) Используя команду /addbot Отправь мне сообщение от Метобота похожее на это:
    /addbot
    Success
    botId: 000000001
    nick: testbot
    token: 000.111111111.22222222222:333333333
    5) Напиши @metabot: /setjoingroups - Разреши добавлять бота в беседы
    6) Напиши имя бота
    7) Напиши enable
    8) Добавьте бота в беседу
    9) Не забудьте разрешить боту писать сообщения в чат
    8) Профит!
"""
    bot.send_text(chat_id=event.data["chat"]["chatId"], text=text)


@init_user_bot
def default_cm(bot, event, user_info):
    if event.data["chat"]["type"] == "private":
        try:
            photo = event.data['parts'][0]["payload"]["fileId"]
        except:
            photo = False
        if photo:
            text = ''
            try:
                text = event.data['parts'][0]["payload"]["caption"]
            except:
                main_message(bot, event.data)
                return
            if re.match(r'/anon', text):
                if len(text) > 6:
                    add_new_post(bot, event.data, text[6:], "anon", photo)
                else:
                    add_new_post(bot, event.data, "", "anon", photo)
            elif re.match(r'/public', text):
                if len(text) > 8:
                    add_new_post(bot, event.data, text[8:], "public", photo)
                else:
                    add_new_post(bot, event.data, "", "public", photo)
            else:
                main_message(bot, event.data)
        elif re.match(r'/anon', event.data["text"]):
            if len(event.data["text"]) > 6:
                text = event.data["text"][6:]
                add_new_post(bot, event.data, text, "anon")
            else:
                message = "Ты забыл написать текст поста :)"
                bot.send_text(chat_id=event.data["chat"]["chatId"], text=message)
                main_message(bot, event.data)
        elif re.match(r'/public', event.data["text"]):
            if len(event.data["text"]) > 8:
                text = event.data["text"][8:]
                add_new_post(bot, event.data, text, "public")
            else:
                message = "Ты забыл написать текст поста :)"
                bot.send_text(chat_id=event.data["chat"]["chatId"], text=message)
                main_message(bot, event.data)
        elif user_info["is_admin"]:
            if re.match(r'/unread', event.data["text"]):
                check_post(bot, event.data)
            else:
                main_message(bot, event.data)
        else:
            main_message(bot, event.data)


@init_user_bot
def admin_cm(bot, event, user_info=None):
    update_admin(bot, event.data, event.data["text"][7:], "add")


@init_user_bot
def noadmin_cm(bot, event, user_info=None):
    update_admin(bot, event.data, event.data["text"][9:], "remove")


@init_user_bot
def setpublic_cm(bot, event, user_info=None):
    set_public(bot, event.data, event.data["text"][11:])


@init_user_bot
def myid_cm(bot, event, user_info=None):
    bot.send_text(chat_id=event.data["chat"]["chatId"], text=event.data["chat"]["chatId"])
        


def main_message(bot, data):
    text = """
        Дорогой друг!
        Чтобы предложить новый пост, напиши одну из следующих команд:
        /public *Текст поста* - Предложить пост публично
        /anon *Текст поста* - Предложить пост анонимно
        Знак звездочки * ставить не нужно

        Если хочешь прикрепить картинку, прикрепляй их по одной с командами для добавления постов
    """
    bot.send_text(chat_id=data["chat"]["chatId"], text=text)


def add_new_post(bot, data, text, post_type, photo=""):
    new_id = database.add_post(
        text, data["timestamp"], post_type, data["chat"]["chatId"], bot.token, photo)
    message = """
    Твой пост был успешно предложен :)
    """
    admins = database.get_admin(bot.token)
    for admin in admins:
        inlineKeyboardMarkup = json.dumps([
            [{"text": "Опубликовать",
                "callbackData": "func_post_"+str(new_id)}],
            [{"text": "Не публиковать",
                "callbackData": "func_delete_"+str(new_id)}]
        ])
        if post_type == "public":
            info = database.check_user(data["chat"]["chatId"])
            text = text + "\n\nАвтор: " + \
                info["first_name"] + " " + info["last_name"]
        if photo:
            if text == "":
                bot.send_file(chat_id=admin, file_id=photo,
                              inline_keyboard_markup=inlineKeyboardMarkup)
            else:
                bot.send_file(chat_id=admin, caption=text, file_id=photo,
                              inline_keyboard_markup=inlineKeyboardMarkup)
        else:
            bot.send_text(chat_id=admin, text=text,
                          inline_keyboard_markup=inlineKeyboardMarkup)
    bot.send_text(chat_id=data["chat"]["chatId"], text=message)


def check_post(bot, data):
    post = database.get_post_public(bot.token)
    if post:
        text = post[1]
        id_post = post[0]
        inlineKeyboardMarkup = json.dumps([
            [{"text": "Опубликовать",
                "callbackData": "func_post_"+str(id_post)}],
            [{"text": "Не публиковать",
                "callbackData": "func_delete_"+str(id_post)}]
        ])
        if post[7]:
            if text == "":
                bot.send_file(chat_id=data["chat"]["chatId"], file_id=post[7],
                              inline_keyboard_markup=inlineKeyboardMarkup)
            else:
                bot.send_file(chat_id=data["chat"]["chatId"], caption=text,
                              file_id=post[7], inline_keyboard_markup=inlineKeyboardMarkup)
        else:
            bot.send_text(chat_id=data["chat"]["chatId"], text=text,
                          inline_keyboard_markup=inlineKeyboardMarkup)
    else:
        text = "Новых постов нету :)"
        bot.send_text(chat_id=data["chat"]["chatId"], text=text)


def set_public(bot, data, text):
    text_arr = text.split(" ")
    secret_key = database.check_public(bot.token)["seq_key"]
    if text_arr[0] == secret_key:
        database.set_public(bot.token, text_arr[1])
        message = "Паблик успешно изменен"
    else:
        message = "Ключ безопасности не совпадает"
    bot.send_text(chat_id=data["chat"]["chatId"], text=message)


def update_admin(bot, data, text, req_type):
    text_arr = text.split(" ")
    secret_key = database.check_public(bot.token)["seq_key"]
    if text_arr[0] == secret_key:
        if req_type == "add":
            database.add_admin(text_arr[1], bot.token)
            message = "Админ был успешно добавлен"
        else:
            database.remove_admin(text_arr[1], bot.token)
            message = "Админ был успешно удален"
    else:
        message = "Ключ безопасности не совпадает"
    bot.send_text(chat_id=data["chat"]["chatId"], text=message)


def button_processing(bot, event):
    data = event.data
    if "func_post" in data["callbackData"]:
        id_post = data["callbackData"][10:]
        post_process(bot, id_post, data, "post")
    elif "func_delete" in data["callbackData"]:
        id_post = data["callbackData"][12:]
        post_process(bot, id_post, data, "delete")


def post_process(bot, id_post, data, proc_type):
    chat_id = database.check_public(bot.token)["chat"]
    if chat_id == "chat":
        text = "Паблик не обазначен\n\nУстанови чат командой /setpublic *Ключ доступа* *id паблика*"
        bot.send_text(chat_id=data["message"]["chat"]["chatId"], text=text)
    else:
        post = database.get_post(id_post)
        database.update_message(id_post)
        if post:
            if post[2] == "non_posted":
                if proc_type == "delete":
                    admin_text = "Пост успешно удален"
                    bot.send_text(
                        chat_id=data["message"]["chat"]["chatId"], text=admin_text)
                    return
                text = post[1]
                admin_text = "Пост успешно опубликован"
                if post[7]:
                    if text == "":
                        bot.send_file(chat_id=chat_id, file_id=post[7])
                    else:
                        bot.send_file(chat_id=chat_id,
                                      caption=text, file_id=post[7])
                else:
                    bot.send_text(chat_id=chat_id, text=text)
            else:
                admin_text = "Данный пост уже обработан"
            bot.send_text(chat_id=data["message"]
                          ["chat"]["chatId"], text=admin_text)
