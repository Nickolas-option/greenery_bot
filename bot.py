import logging
import random

from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher.filters.state import State, StatesGroup

API_TOKEN = '6758375137:AAFosYicJRZd5C6AJYlzojaoxHAdpEOlTNM'
logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)


class TrackingState(StatesGroup):
    waiting_for_stock_symbol = State()
    waiting_for_interval = State()


@dp.message_handler(commands=['start'])
async def welcome(message: types.Message):
    welcome_text = "Привет! Я бот, который поможет вам с разными действиями с ценными бумагами.\n" \
                   "Введите /help, чтобы посмотреть, чем я могу вам помочь! "
    await bot.send_message(message.chat.id, welcome_text)


@dp.message_handler(commands=['help'])
async def help_command(message: types.Message):
    help_text = "Доступные команды:\n\n" \
                "/start - Начать взаимодействие💰\n" \
                "/actions - Показать доступные действия👀\n" \
                "/parrot - Посмотреть на попугая🦜\n" \
                "/help - Показать это сообщение🤯"
    await message.answer(help_text)


@dp.message_handler(commands=['actions'])
async def show_actions_keyboard(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    buttons = ["Запросить стоимость акции", "Предсказать стоимость акции", "Поставить акцию на отслеживание"]
    keyboard.add(*buttons)
    await bot.send_message(message.chat.id, "Выберите действие:", reply_markup=keyboard)

    @dp.message_handler(lambda message1: message1.text == "Поставить акцию на отслеживание")
    async def start_tracking(message1: types.Message):
        keyboard_stocks = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        buttons_stocks = ["Apple", "Google", "Microsoft"]
        keyboard_stocks.add(*buttons_stocks)
        await bot.send_message(message.chat.id, "Какую акцию вы хотите поставить на отслеживание?",
                               reply_markup=keyboard_stocks)

        @dp.message_handler(lambda message2: message2.text in buttons_stocks)
        async def time_tracking(message2: types.Message):
            keyboard_for_tracking = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            buttons_time_for_tracking = ["30 минут", "2 часа", "Сутки"]
            keyboard_for_tracking.add(*buttons_time_for_tracking)
            await bot.send_message(message.chat.id,
                                   f"Вы выбрали акцию {message2.text}. Как часто вы хотите отслеживать стоимость акции?",
                                   reply_markup=keyboard_for_tracking)

            @dp.message_handler(lambda message3: message3.text in buttons_time_for_tracking)
            async def process_interval(message3: types.Message):
                response_text = f"Акция {message2.text} поставлена на отслеживание с интервалом {message3.text}."
                await bot.send_message(message.chat.id, response_text)


@dp.message_handler(lambda message: message.text == "Запросить стоимость акции")
async def stock_price_request(message: types.Message):
    response_text = "Стоймость акции: $100"
    await bot.send_message(message.chat.id, response_text)


@dp.message_handler(lambda message: message.text == "Предсказать стоимость акции")
async def predict_stock_price(message: types.Message):
    response_text = "Предсказанная стоймость акции: $120"
    await bot.send_message(message.chat.id, response_text)


@dp.message_handler(commands=['parrot'])
async def send_random_parrot(message: types.Message):
    parrot_number = random.randint(1, 16)
    parrot_filename = f'data/parrots/parrot{parrot_number}.jpeg'

    with open(parrot_filename, 'rb') as photo:
        await bot.send_photo(message.chat.id, photo, caption='Случайный попугай 🦜', reply_to_message_id=message.message_id)

@dp.message_handler()
async def unknown_message(message: types.Message):
    response_text = "Мы пока не умеем отвечать на такое сообщение. \n" \
                    "Чтобы посмотреть доступные команды, напишите /help."
    await bot.send_message(message.chat.id, response_text)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
