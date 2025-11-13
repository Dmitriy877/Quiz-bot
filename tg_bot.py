from environs import env
import logging
import json
import random
import os

from functools import partial
import telegram
import redis
from telegram import Update, ForceReply, ReplyKeyboardMarkup
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, CallbackContext, RegexHandler, ConversationHandler)


def start(update: Update, context: CallbackContext, CHOOSING) -> int:
    """Send a message when the command /start is issued."""
    custom_keyboard = [['Новый вопрос', 'Сдаться'], ['Мой счет']]
    reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard)
    context.bot.send_message(chat_id=update.effective_chat.id, text="Привет! Я бот для викторин", reply_markup=reply_markup)
    return CHOOSING


def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    update.message.reply_text('Help!')


def handle_new_question_request(update: Update, context: CallbackContext, TYPING_REPLY, collect_quiz, r) -> int:
    chat_id = update.effective_chat.id
    random_question = random.choice(list(collect_quiz.keys()))
    r.set(chat_id, random_question)
    context.bot.send_message(
            chat_id=chat_id,
            text=random_question,
        )
    return TYPING_REPLY

def handle_send_answer(update: Update, context: CallbackContext, CHOOSING, r, collect_quiz) -> int:
    chat_id = update.effective_chat.id
    answer = collect_quiz[r.get(chat_id)]
    custom_keyboard = [['Новый вопрос', 'Сдаться'], ['Мой счет']]
    reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard)
    context.bot.send_message(
            chat_id=chat_id,
            text=answer,
            reply_markup=reply_markup
        )
    return CHOOSING


def handle_solution_attempt(update: Update, context: CallbackContext, TYPING_REPLY, CHOOSING, r) -> int:
    chat_id = update.effective_chat.id
    guess_question = update.message.text.split('.')
    answer = r.get(chat_id)
    custom_keyboard = [['Новый вопрос', 'Сдаться'], ['Мой счет']]
    reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard)

    if guess_question[0] in answer:
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
    
    
    r = redis.Redis(host='localhost', port=6379, db=0, charset='utf-8', decode_responses=True, protocol=3)

    with open('quiz_data.json', 'r', encoding='utf-8') as file:
        collect_quiz = json.load(file)

    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
    )

    logger = logging.getLogger(__name__)

    telegram_bot_token = env.str('TELEGRAM_BOT_TOKEN')

    CHOOSING, TYPING_REPLY = range(2)
    
    start_with_arguments = partial(start, CHOOSING=CHOOSING)
    handle_new_question_request_with_arguments = partial(handle_new_question_request, TYPING_REPLY=TYPING_REPLY, collect_quiz=collect_quiz, r=r)
    handle_solution_attempt_with_arguments = partial(handle_solution_attempt, TYPING_REPLY=TYPING_REPLY, CHOOSING=CHOOSING, r=r)
    handle_send_answer_with_arguments = partial(handle_send_answer, CHOOSING=CHOOSING, r=r, collect_quiz=collect_quiz)

    updater = Updater(telegram_bot_token)

    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(

        entry_points = [CommandHandler('start', start_with_arguments)],

        states = {
            CHOOSING: [RegexHandler('^(Новый вопрос)$',
                                    handle_new_question_request_with_arguments,
                                    pass_user_data=True)
                       ],

            TYPING_REPLY: [
                
                MessageHandler(Filters.text('Сдаться'), handle_send_answer_with_arguments, pass_user_data=True),
                MessageHandler(Filters.text & ~Filters.command, partial(handle_solution_attempt_with_arguments)),
                           ],
                  },

        fallbacks=[]

    )

    dispatcher.add_handler(conv_handler)

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
