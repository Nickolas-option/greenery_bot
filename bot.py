import asyncio
import json
import logging
import os
import random
 
from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
 
# Logger initialization and logging level setting
log = logging.getLogger(__name__)
log.setLevel(os.environ.get('LOGGING_LEVEL', 'INFO').upper())
 
API_TOKEN = 'TOKEN'  
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
 
 
# Handlers
async def welcome(message: types.Message):
    welcome_text = "Привет! Я бот, который поможет вам с разными действиями с ценными бумагами.\n" \
                   "Введите /help, чтобы посмотреть, чем я могу вам помочь! "
    await bot.send_message(message.chat.id, welcome_text)
 
 
async def help_command(message: types.Message):
    help_text = "Доступные команды:\n\n" \
                "/start - Начать взаимодействие💰\n" \
                "/actions - Показать доступные действия👀\n" \
                "/parrot - Посмотреть на попугая🦜\n" \
                "/help - Показать это сообщение🤯"
    await message.answer(help_text)
 
 
async def show_actions_keyboard(message: types.Message, state: FSMContext):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    buttons = ["Запросить стоимость акции", "Предсказать стоимость акции", "Поставить акцию на отслеживание"]
    keyboard.add(*buttons)
    await bot.send_message(message.chat.id, "Выберите действие:", reply_markup=keyboard)
 
 
async def start_tracking(message: types.Message):
    response_text = f"Акция {message.text} была поставлена на отслеживание."
    await bot.send_message(message.chat.id, response_text)
 
 
async def stock_price_request(message: types.Message):
    response_text = "Стоимость акции: $100"
    await bot.send_message(message.chat.id, response_text)
 
 
async def predict_stock_price(message: types.Message):
    response_text = "Предсказанная стоимость акции: $120"
    await bot.send_message(message.chat.id, response_text)
 
 
async def send_random_parrot(message: types.Message):
    parrot_number = random.randint(1, 16)
    parrot_filename = f'greenery_bot-main/data/parrots/parrot{parrot_number}.jpeg'
 
    with open(parrot_filename, 'rb') as photo:
        await bot.send_photo(message.chat.id, photo, caption='Случайный попугай 🦜',
                             reply_to_message_id=message.message_id)
 
 
async def unknown_message(message: types.Message):
    response_text = "Мы пока не умеем отвечать на такое сообщение. \n" \
                    "Чтобы посмотреть доступные команды, напишите /help."
    await bot.send_message(message.chat.id, response_text)
 
 
# Functions for Yandex.Cloud
async def register_handlers(dp: Dispatcher):
    """Registration all handlers before processing update."""
    dp.register_message_handler(welcome, commands=['start'])
    dp.register_message_handler(help_command, commands=['help'])
    dp.register_message_handler(show_actions_keyboard, commands=['actions'])
    dp.register_message_handler(start_tracking, lambda message: message.text == "Поставить акцию на отслеживание")
    dp.register_message_handler(stock_price_request, lambda message: message.text == "Запросить стоимость акции")
    dp.register_message_handler(predict_stock_price, lambda message: message.text == "Предсказать стоимость акции")
    dp.register_message_handler(send_random_parrot, commands=['parrot'])
    dp.register_message_handler(unknown_message)
 
    log.debug('Handlers are registered.')
 
 
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
 
 
async def handler(event, context):
    if event['httpMethod'] == 'POST':
        # Bot and dispatcher initialization
        bot = Bot(token=API_TOKEN)
        dp = Dispatcher(bot)
 
        await register_handlers(dp)
        await process_event(event, dp)
 
        return {'statusCode': 200, 'body': 'ok'}
    return {'statusCode': 200, 'body': 'ok'}
