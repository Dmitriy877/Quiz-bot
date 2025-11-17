import random
import json

import logging
from logging.handlers import RotatingFileHandler
import vk_api as vk
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from environs import env
import redis
import telegram

from collect_quiz_in_file import collect_quiz_in_file

class TelegramLogsHandler(logging.Handler):
    def __init__(self, log_bot, chat_id):
        super().__init__()
        self.chat_id = chat_id
        self.log_bot = log_bot

    def emit(self, record):
        log_entry = self.format(record)
        self.log_bot.send_message(chat_id=self.chat_id, text=log_entry)


def start(event, vk_api, keyboard):
    vk_api.messages.send(
        user_id=event.user_id,
        keyboard=keyboard.get_keyboard(),
        message="Привет! Я бот для викторин",
        random_id=random.randint(1, 1000)
    )


def send_new_message(event, vk_api, collect_quiz, keyboard, r):
    random_question = random.choice(list(collect_quiz.keys()))
    chat_id = event.user_id
    r.set(chat_id, random_question)
    text = [random_question]
    vk_api.messages.send(
        user_id=chat_id,
        message=text,
        random_id=random.randint(1, 1000),
        keyboard=keyboard.get_keyboard()
    )


def send_answer(event, vk_api, collect_quiz, keyboard, r):
    chat_id = event.user_id
    answer = str(collect_quiz[r.get(chat_id)])
    vk_api.messages.send(
        user_id=chat_id,
        message=answer,
        random_id=random.randint(1, 1000),
        keyboard=keyboard.get_keyboard()
    )
    r.delete(chat_id)


def guess_question(event, vk_api, collect_quiz, keyboard, r):
    chat_id = event.user_id
    guess_question = event.text.split(' ')
    if r.exists(chat_id):
        answer = collect_quiz[r.get(chat_id)]
        if guess_question[0] in answer:
            vk_api.messages.send(
                user_id=chat_id,
                message='Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос»',
                random_id=random.randint(1, 1000),
                keyboard=keyboard.get_keyboard()
            )
            r.delete(chat_id)
        else:
            vk_api.messages.send(
                user_id=chat_id,
                message='Неправильно… Попробуешь ещё раз?',
                random_id=random.randint(1, 1000),
                keyboard=keyboard.get_keyboard()
            )


def main():

    env.read_env()

    telegram_bot_token = env.str('TELEGRAM_BOT_TOKEN')
    chat_id = env.str('TELEGRAM_CHAT_ID')
    vk_group_token = env.str('VK_API_KEY')
    quiz_questions_filefolder_name = env.str('QUIZ_QUESTIONS_FILEFOLDER_NAME')
    collect_quiz = collect_quiz_in_file(quiz_questions_filefolder_name)
    r = redis.Redis(host='localhost', port=6379, db=0, charset='utf-8', decode_responses=True, protocol=3)

    log_bot = telegram.Bot(token=telegram_bot_token)
    logger = logging.getLogger('vk_bot_loger')
    logger.setLevel(logging.INFO)
    logger.addHandler(RotatingFileHandler('vk_bot_log.log', maxBytes=200, backupCount=2))
    logger.addHandler(TelegramLogsHandler(log_bot, chat_id))

    vk_session = vk.VkApi(token=vk_group_token)
    vk_api = vk_session.get_api()

    keyboard = VkKeyboard(one_time=True)

    keyboard.add_button('Новый вопрос', color=VkKeyboardColor.POSITIVE)
    keyboard.add_button('Сдаться', color=VkKeyboardColor.NEGATIVE)

    keyboard.add_line()
    keyboard.add_button('Мой счет', color=VkKeyboardColor.PRIMARY)

    longpoll = VkLongPoll(vk_session)

    try:
        for event in longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                if event.text == 'Старт':
                    start(event, vk_api, keyboard)

                if event.text == 'Новый вопрос':
                    send_new_message(event, vk_api, collect_quiz, keyboard, r)

                if event.text == 'Сдаться':
                    send_answer(event, vk_api, collect_quiz, keyboard, r)
                guess_question(event, vk_api, collect_quiz, keyboard, r)

    except Exception as error:
        logger.exception(f'VK Bot Has been crashed with error {error}')


if __name__ == '__main__':
    main()
