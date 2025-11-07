from environs import env
import logging
import json
import random

from functools import partial
import telegram
from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext


def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    context.bot.send_message(chat_id=update.effective_chat.id, text="Привет! Я бот для викторин")


def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    update.message.reply_text('Help!')


def echo(update: Update, context: CallbackContext, collect_quiz) -> None:
    """Echo the user message."""
    random_question = random.choice(list(collect_quiz.keys()))
    chat_id = update.effective_chat.id
    custom_keyboard = [['Новый вопрос', 'Сдаться'], ['Мой счет']]
    reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard)
    if update.message.text == 'Новый вопрос':
        context.bot.send_message(
            chat_id=chat_id,
            text=random_question,
            reply_markup=reply_markup
        )
    else:
        context.bot.send_message(
            chat_id=chat_id,
            text='Функция не подключена',
            reply_markup=reply_markup
        )


def main() -> None:
    env.read_env()
    telegram_bot_token = env.str('TELEGRAM_BOT_TOKEN')

    with open('quiz_data.json', 'r', encoding='utf-8') as file:
        collect_quiz = json.load(file)

    send_quiz_message_with_arguments = partial(echo, collect_quiz=collect_quiz)

    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
    )
    logger = logging.getLogger(__name__)

    updater = Updater(telegram_bot_token)

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))

    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, send_quiz_message_with_arguments))

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
