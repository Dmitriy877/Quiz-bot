import random
from functools import partial

import logging
from logging.handlers import RotatingFileHandler
import telegram
import redis
from environs import env
from telegram import Update
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext,
    RegexHandler,
    ConversationHandler
)

from collect_quiz_in_file import collect_quiz_in_file


class TelegramLogsHandler(logging.Handler):
    def __init__(self, log_bot, chat_id):
        super().__init__()
        self.chat_id = chat_id
        self.log_bot = log_bot

    def emit(self, record):
        log_entry = self.format(record)
        self.log_bot.send_message(chat_id=self.chat_id, text=log_entry)


def start(update: Update, context: CallbackContext, CHOOSING: int) -> int:
    """Send a message when the command /start is issued."""
    custom_keyboard = [['Новый вопрос', 'Сдаться'], ['Мой счет']]
    reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard)
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Привет! Я бот для викторин",
        reply_markup=reply_markup
    )
    return CHOOSING


def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    update.message.reply_text('Help!')


def handle_new_question_request(
    update: Update,
    context: CallbackContext,
    TYPING_REPLY: int,
    collect_quiz: dict,
    redis_config
) -> int:

    chat_id = update.effective_chat.id
    random_question = random.choice(list(collect_quiz.keys()))
    redis_config.set(chat_id, random_question)
    context.bot.send_message(
            chat_id=chat_id,
            text=random_question,
        )
    return TYPING_REPLY


def handle_send_answer(
    update: Update,
    context: CallbackContext,
    CHOOSING: int,
    redis_config,
    collect_quiz: dict
) -> int:

    chat_id = update.effective_chat.id
    answer = collect_quiz[redis_config.get(chat_id)]
    custom_keyboard = [['Новый вопрос', 'Сдаться'], ['Мой счет']]
    reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard)
    context.bot.send_message(
            chat_id=chat_id,
            text=answer,
            reply_markup=reply_markup
        )
    return CHOOSING


def handle_solution_attempt(
    update: Update,
    context: CallbackContext,
    TYPING_REPLY: int,
    CHOOSING: int,
    redis_config,
    collect_quiz: dict
) -> int:

    chat_id = update.effective_chat.id
    user_answer = update.message.text.split('.')
    answer = collect_quiz[redis_config.get(chat_id)]
    custom_keyboard = [['Новый вопрос', 'Сдаться'], ['Мой счет']]
    reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard)

    if user_answer[0] in answer:
        context.bot.send_message(
            chat_id=chat_id,
            text='Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос»',
            reply_markup=reply_markup
        )
        return CHOOSING

    else:
        context.bot.send_message(
            chat_id=chat_id,
            text='Неправильно… Попробуешь ещё раз?',
            reply_markup=reply_markup
        )

        return TYPING_REPLY


def main() -> None:

    env.read_env()

    telegram_bot_token = env.str('TELEGRAM_BOT_TOKEN')
    chat_id = env.str('TELEGRAM_CHAT_ID')
    quiz_questions_filefolder_name = env.str('QUIZ_QUESTIONS_FILEFOLDER_NAME')
    collect_quiz = collect_quiz_in_file(quiz_questions_filefolder_name)
    redis_host = env.str('REDIS_HOST')
    redis_port = env.int('REDIS_PORT')
    redis_database = env.int('REDIS_DATABASE')
    redis_protocol = env.int('REDIS_PROTOCOL')
    redis_charset = env.str('REDIS_CHARSET')

    redis_config = redis.Redis(
        host=redis_host,
        port=redis_port,
        db=redis_database,
        charset=redis_charset,
        decode_responses=True,
        protocol=redis_protocol
    )

    log_bot = telegram.Bot(token=telegram_bot_token)
    logger = logging.getLogger('tg_bot_loger')
    logger.setLevel(logging.INFO)
    logger.addHandler(TelegramLogsHandler(log_bot, chat_id))
    logger.addHandler(RotatingFileHandler(
        'tg_bot_log.log',
        maxBytes=200,
        backupCount=2
    ))

    CHOOSING, TYPING_REPLY = range(2)

    start_with_arguments = partial(start, CHOOSING=CHOOSING)

    handle_new_question_request_with_arguments = partial(
        handle_new_question_request,
        TYPING_REPLY=TYPING_REPLY,
        collect_quiz=collect_quiz,
        redis_config=redis_config
    )

    handle_solution_attempt_with_arguments = partial(
        handle_solution_attempt,
        TYPING_REPLY=TYPING_REPLY,
        CHOOSING=CHOOSING,
        redis_config=redis_config,
        collect_quiz=collect_quiz
    )

    handle_send_answer_with_arguments = partial(
        handle_send_answer,
        CHOOSING=CHOOSING,
        redis_config=redis_config,
        collect_quiz=collect_quiz
    )

    updater = Updater(telegram_bot_token)
    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(

        entry_points=[CommandHandler('start', start_with_arguments)],
        states={
            CHOOSING: [RegexHandler('^(Новый вопрос)$',
                                    handle_new_question_request_with_arguments,
                                    pass_user_data=True)
            ],

            TYPING_REPLY: [

                MessageHandler(
                    Filters.text('Сдаться'),
                    handle_send_answer_with_arguments,
                    pass_user_data=True
                ),
                MessageHandler(
                    Filters.text & ~Filters.command,
                    partial(handle_solution_attempt_with_arguments)
                ),
            ],
        },
        fallbacks=[]
    )

    dispatcher.add_handler(conv_handler)

    try:
        updater.start_polling()
        updater.idle()
    except Exception as error:
        logger.exception(f'TG Bot Has been crashed with error {error}')


if __name__ == '__main__':
    main()
