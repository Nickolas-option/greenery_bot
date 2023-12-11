import asyncio
import json
import logging
import os
import random
from yahoo_fin import stock_info

from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
    
# Logger initialization and logging level setting
log = logging.getLogger(__name__)
log.setLevel(os.environ.get('LOGGING_LEVEL', 'INFO').upper())
API_TOKEN = '6758375137:AAFosYicJRZd5C6AJYlzojaoxHAdpEOlTNM'
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)


# Handlers
async def welcome(message: types.Message):
    welcome_text = "Привет! Я бот, который поможет вам с разными действиями с ценными бумагами.\n" \
                   "Введите /help, чтобы посмотреть, чем я могу вам помочь! "
    await bot.send_message(message.chat.id, welcome_text)


async def help_command(message: types.Message):
    help_text = "Доступные команды:\n\n" \
                "/start - Начать взаимодействие 💰\n" \
                "/getprice - Получить текущую стоимость акции 👀\n" \
                "/parrot - Посмотреть на попугая 🦜\n" \
                "/help - Показать это сообщение 🤯"
    await message.answer(help_text)


async def send_random_parrot(message: types.Message):
    parrot_number = random.randint(1, 16)
    parrot_filename = f'greenery_bot-main/data/parrots/parrot{parrot_number}.jpeg'

    with open(parrot_filename, 'rb') as photo:
        await bot.send_photo(message.chat.id, photo, caption='Случайный попугай 🦜',
                             reply_to_message_id=message.message_id)


async def get_stock_price(message: types.Message):
    try:
        log.debug(f"Выполняется get_stock_price для сообщения: {message}")

        # Разбиваем команду, чтобы получить символ акции
        command_parts = message.text.split()

        # Проверяем, предоставил ли пользователь символ акции
        if len(command_parts) < 2:
            raise IndexError("Не указан символ акции")

        # Извлекаем символ акции из команды
        stock_symbol = command_parts[1].upper()

        # Получаем данные о цене акции с использованием yahoo_fin
        current_price = stock_info.get_live_price(stock_symbol)

        # Отвечаем текущей ценой акции
        response_text = f"Последняя известная стоимость акции {stock_symbol}: ${current_price:.2f}"
        await bot.send_message(message.chat.id, response_text)

    except IndexError:
        # Если пользователь не предоставил символ акции
        error_message = "Пожалуйста, укажите тикер акции после команды /getprice. Например: \n" \
                        "/getprice AAPL"
        await bot.send_message(message.chat.id, error_message)

    except Exception as e:
        # Если произошла ошибка при получении цены акции
        error_message = f"Произошла ошибка при получении цены акции: {str(e)}"
        await bot.send_message(message.chat.id, error_message)
        logging.error(error_message)



async def unknown_message(message: types.Message):
    response_text = "Мы пока не умеем отвечать на такое сообщение. \n" \
                    "Чтобы посмотреть доступные команды, напишите /help."
    await bot.send_message(message.chat.id, response_text)


# Функция для Yandex.Cloud
async def register_handlers(dp: Dispatcher):
    """Registration all handlers before processing update."""
    dp.register_message_handler(welcome, commands=['start'])
    dp.register_message_handler(help_command, commands=['help'])
    dp.register_message_handler(send_random_parrot, commands=['parrot'])
    dp.register_message_handler(get_stock_price, commands=['getprice'])
    dp.register_message_handler(unknown_message)

    log.debug('Handlers are registered.')

# Функция для Yandex.Cloud
async def process_event(event, dp: Dispatcher):
    """
    Converting a Yandex.Cloud functions event to an update and
    handling the update.
    """

    update = json.loads(event['body'])
    log.debug('Update: ' + str(update))

    Bot.set_current(dp.bot)
    update = types.Update.to_object(update)
    await dp.process_update(update)

# Функция для Yandex.Cloud
async def handler(event, context):
    if event['httpMethod'] == 'POST':
        # Bot and dispatcher initialization
        bot = Bot(token=API_TOKEN)
        dp = Dispatcher(bot)

        await register_handlers(dp)
        await process_event(event, dp)

        return {'statusCode': 200, 'body': 'ok'}
    return {'statusCode': 200, 'body': 'ok'}
