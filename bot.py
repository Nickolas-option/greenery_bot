import asyncio
from typing import Dict
from dateutil.relativedelta import relativedelta
import json
from decimal import Decimal
import logging
import os
from aiogram.types import Message
import datetime
from datetime import timedelta
import numpy as np
import os
import pandas as pd
import time
import yahoo_fin.stock_info as si
import random
from aiogram import types, Dispatcher, Bot
from datetime import datetime
import aioschedule
import asyncio
from boto3.dynamodb.conditions import Key
from decimal import Decimal, ROUND_HALF_UP
import yahoo_fin.stock_info as si
import matplotlib.pyplot as plt
from prophet import Prophet
from datetime import datetime, timedelta
from io import BytesIO
from yahoo_fin import stock_info
from aiogram import Bot, Dispatcher, types
from aiogram.utils.markdown import code
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
import json
import logging
import os
import boto3
from botocore.exceptions import ClientError

dynamodb = boto3.resource(
    'dynamodb',
    endpoint_url="https://docapi.serverless.yandexcloud.net/ru-central1/b1g5ma3co0segbkhov3q/etngltj5g02bud0hv3ho",
    region_name='us-east-1',
    aws_access_key_id="YCAJEmJXKGtf9CY0don6scA6f",
    aws_secret_access_key="YCNlhuXkX_MgMZ9Q9kliPo15Q7wKH5_rwy2gIs0q"
)

# Logger initialization and logging level setting
log = logging.getLogger(__name__)
log.setLevel(os.environ.get('LOGGING_LEVEL', 'INFO').upper())
API_TOKEN = '6758375137:AAFosYicJRZd5C6AJYlzojaoxHAdpEOlTNM'
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Темная тема для графиков
plt.style.use('dark_background')


######################
# Класс для парсинга и создания csv с историей
class Parser:
    def __init__(self, stock_file_name_constructor, requests_filename, stock_df_header,
                 first_request_history_days=1095):
        self.request_id = 0

        self.last_request_dict = {}

        self.stock_file_name_constructor = stock_file_name_constructor

        self.requests_filename = requests_filename
        self.stock_df_header = stock_df_header
        self.update_threshold = relativedelta(days=1)  # дельта дней
        self.first_request_history_days = first_request_history_days

    async def update_history(self):
        self.request_id += 1
        current_date = datetime.datetime.now()
        error_message = " 1 \n"
        await bot.send_message(message.chat.id, error_message)

        if (os.path.isfile(self.requests_filename)):
            error_message = " 2 \n"
            await bot.send_message(message.chat.id, error_message)
            requests = open(self.requests_filename, "r")
            requests_heading = requests.readline()

            for raw_row in requests:
                try:
                    error_message = " 3 \n"
                    await bot.send_message(message.chat.id, error_message)
                    row = raw_row.split(",")
                    stock_name = row[0]

                    stock_file_name = self.stock_file_name_constructor(stock_name)
                    if stock_name in self.last_request_dict:

                        start_date = self.last_request_dict[stock_name]
                    else:

                        start_date = current_date - self.first_request_history_days
                        stock_file = open(stock_file_name, "w")
                        stock_file.write(self.stock_df_header)
                        stock_file.close()
                    if (current_date - start_date > self.update_threshold):
                        historical_prices = si.get_data(stock_name, start_date, current_date)
                        historical_prices.to_csv(path_or_buf=stock_file_name, header=False, mode='a')
                        self.last_request_dict[stock_name] = current_date


                except Exception as e:
                    error_message = f"Произошла ошибка при получении цены акции."
                    await bot.send_message(message.chat.id, error_message)

            error_message = " 4 \n"
            await bot.send_message(message.chat.id, error_message)
            requests.close()
            os.remove(self.requests_filename)
            error_message = " 5 \n"
            await bot.send_message(message.chat.id, error_message)


def history_stock_df_name(stock_name):
    return f"greenery_bot-main/data/stocks/history_{stock_name}.csv"


requests_filename = "greenery_bot-main/data/stocks/requests.csv"
stock_df_header = "Datetime,Open,High,Low,Close,Adj Close,Volume,Ticker\n"

default_parser = Parser(stock_file_name_constructor=history_stock_df_name, \
                        requests_filename=requests_filename, \
                        stock_df_header=stock_df_header)


##############################

async def save_stock_alert(telegram_id, current_datetime, stock_name, current_price, percentage, sign):
    dynamodb = boto3.resource(
        'dynamodb',
        endpoint_url="https://docapi.serverless.yandexcloud.net/ru-central1/b1g5ma3co0segbkhov3q/etngltj5g02bud0hv3ho",
        region_name='us-east-1',
        aws_access_key_id="YCAJEmJXKGtf9CY0don6scA6f",
        aws_secret_access_key="YCNlhuXkX_MgMZ9Q9kliPo15Q7wKH5_rwy2gIs0q"
    )

    DYNAMODB_TABLE_NAME = 'StockAlerts'
    existing_tables = dynamodb.meta.client.list_tables()['TableNames']
    if DYNAMODB_TABLE_NAME not in existing_tables:
        table = dynamodb.create_table(
            TableName=DYNAMODB_TABLE_NAME,
            KeySchema=[
                {
                    'AttributeName': 'telegram_id',
                    'KeyType': 'HASH'
                },
                {
                    'AttributeName': 'current_datetime',
                    'KeyType': 'RANGE'
                }
            ],
            AttributeDefinitions=[
                {'AttributeName': 'telegram_id', 'AttributeType': 'S'},
                {'AttributeName': 'current_datetime', 'AttributeType': 'S'},
                {'AttributeName': 'stock_name', 'AttributeType': 'S'},
                {'AttributeName': 'current_price', 'AttributeType': 'N'},
                {'AttributeName': 'percentage', 'AttributeType': 'N'},
                {'AttributeName': 'sign', 'AttributeType': 'N'}
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )

        table.wait_until_exists()

    table = dynamodb.Table(DYNAMODB_TABLE_NAME)

    stock_data = {
        'telegram_id': str(telegram_id),
        'current_datetime': current_datetime,
        'stock_name': stock_name,
        'current_price': Decimal(str(current_price)),
        'percentage': Decimal(str(percentage)),
        'sign': int(sign)
    }

    table.put_item(Item=stock_data)


async def start_monitoring(message: types.Message):
    try:
        log.debug(f"Executing start_monitoring for message: {message}")
        command_parts = message.text.split()
        if len(command_parts) < 2:
            raise IndexError("No stock symbol provided")

        stock_symbol = command_parts[1].upper()
        current_price = stock_info.get_live_price(stock_symbol)
        percentage = 5.0
        sign = 1

        await save_stock_alert(message.from_user.id, str(datetime.now()), stock_symbol, current_price, percentage, sign)
        response_text = f"Успешно запущен мониторинг акции {stock_symbol}. Текущая цена: ${current_price:.2f}"
        await bot.send_message(message.chat.id, response_text)

    except IndexError:
        # Если пользователь не предоставил символ акции
        error_message = "Пожалуйста, укажите тикер акции после команды /start_monitoring.\n" \
                        f"Например: <code>/start_monitoring YNDX</code>."
        await bot.send_message(message.chat.id, error_message, parse_mode="HTML")


    except Exception as e:
        # Если произошла ошибка при получении данных по акции
        error_message = f"Произошла ошибка при вводе.\n" \
                        f"Пожалуйста, укажите тикер акции после команды /start_monitoring.\n" \
                        f"Например: <code>/start_monitoring YNDX</code>."
        await bot.send_message(message.chat.id, error_message, parse_mode="HTML")
        logging.error(error_message)


async def get_stock_alerts(message: types.Message):
    telegram_id = message.from_user.id
    dynamodb = boto3.resource('dynamodb', endpoint_url=DYNAMODB_ENDPOINT,
                              region_name='us-east-1',
                              aws_access_key_id=AWS_ACCESS_KEY_ID,
                              aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
    table = dynamodb.Table(DYNAMODB_TABLE_NAME)
    response = table.query(
        KeyConditionExpression=Key('telegram_id').eq(str(telegram_id))
    )
    stock_alerts = response.get('Items', [])
    return stock_alerts


# Handlers
async def welcome(message: types.Message):
    welcome_text = "Привет! Я бот, который поможет вам с разными действиями с ценными бумагами.\n" \
                   "Введите /help, чтобы посмотреть, чем я могу вам помочь! "
    await bot.send_message(message.chat.id, welcome_text)


async def help_command(message: types.Message):
    help_text = "Доступные команды:\n\n" \
                "/start - Начать взаимодействие💰\n" \
                "/moment_price - Получить текущую стоимость акции👀\n" \
                "/stock_history - Получить график стоимости акции📈\n" \
                "/start_monitoring - Поставить акцию на отслеживание🔎\n" \
                "/predict_price - Получить предсказание стоимости акции🪄\n" \
                "/parrot - Посмотреть на попугая🦜\n" \
                "/help - Показать это сообщение🤯"
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
        error_message = "Чтобы воспользоваться данной функцией,\n" \
                        f"укажите тикер акции после команды /moment_price.\n" \
                        f"Например: <code>/moment_price AAPL</code>."
        await bot.send_message(message.chat.id, error_message, parse_mode="HTML")

    except Exception as e:
        # Если произошла ошибка при получении цены акции
        error_message = f"Произошла ошибка при вводе.\n" \
                        f"Пожалуйста, укажите тикер акции после команды /moment_price.\n" \
                        f"Например: <code>/moment_price AAPL</code>."
        await bot.send_message(message.chat.id, error_message, parse_mode="HTML")
        logging.error(error_message)


###
async def get_live_price(stock_name):
    ticker = yf.Ticker(stock_name)
    data = ticker.history(period='1d')
    if not data.empty:
        live_price = data['Close'].iloc[-1]
        return live_price
    return None


async def display_stranges(user_id, bot):
    table = dynamodb.Table('StockAlerts')
    response = table.query(
        KeyConditionExpression=Key('telegram_id').eq(str(user_id))
    )

    for item in response.get('Items', []):
        stock_name = item['stock_name']
        current_price = await get_live_price(stock_name)

        if current_price is not None:
            percentage = float(item['percentage'])
            sign = int(item['sign'])


async def scheduler(user_id, bot):
    aioschedule.every().day.at("12:00").do(display_stranges, user_id, bot)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)


# async def on_startup(dp):
#     # Fetch all unique telegram_ids from the database
#     # Replace 'Users' with your actual DynamoDB table name
#     users_table = dynamodb.Table('Users')
#     response = users_table.scan(ProjectionExpression='telegram_id')
#     telegram_ids = {int(item['telegram_id']) for item in response.get('Items', [])}

#     # Initialize bot and dispatcher for each user
#     for user_id in telegram_ids:
#         user_bot = Bot(token=API_TOKEN)
#         user_dp = Dispatcher(user_bot)

#         # Register user-specific scheduler
#         asyncio.create_task(scheduler(user_id, user_bot))

#     return {'statusCode': 200, 'body': 'ok'}
###

async def get_stock_history(message: types.Message):
    try:
        # Получаем символ акции и количество дней из сообщения пользователя
        command_parts = message.text.split()
        if len(command_parts) < 3:
            raise ValueError("Неверная команда. Используйте /stock_history SYMBOL DAYS")

        stock_symbol = command_parts[1].upper()
        num_days = int(command_parts[2])

        # Получаем исторические цены акции за указанное количество дней
        end_date = datetime.now()
        start_date = end_date - relativedelta(days=num_days)  # кол-во дней (дельта дней)
        historical_prices = si.get_data(stock_symbol, start_date, end_date)

        # Строим график исторических цен
        plot_title = f"История цен акции {stock_symbol} за последние {num_days} дней"
        plt.figure(figsize=(10, 6))
        plt.plot(historical_prices.index, historical_prices['close'], marker='o', linestyle='-')
        plt.title(plot_title)
        plt.xlabel('Дата')
        plt.ylabel('Цена закрытия ($)')
        plt.grid(True)

        # Сохраняем график в объект BytesIO
        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png')
        img_buffer.seek(0)

        # Отправляем график как фото пользователю
        await bot.send_photo(message.chat.id, photo=img_buffer)

        # Закрываем график для освобождения ресурсов
        plt.close()

    except ValueError as ve:
        # Обрабатываем ошибку неверной команды
        error_message = "Чтобы воспользоваться данной функцией, укажите акцию и количество дней,\n" \
                        f"за которое вас интересует её график.\n" \
                        f"Например: <code>/stock_history TSLA 14</code>."
        await bot.send_message(message.chat.id, error_message, parse_mode="HTML")

    except Exception as e:
        # Обрабатываем другие исключения (например, ошибки при получении данных)
        error_message = f"Произошла ошибка при вводе.\n" \
                        f"Пожалуйста, укажите акцию и количество дней, за которое вас интересует её график.\n" \
                        f"Например: <code>/stock_history TSLA 14</code>."
        await bot.send_message(message.chat.id, error_message, parse_mode="HTML")


async def get_stock_predict(message: types.Message):
    try:
        command_parts = message.text.split()
        if len(command_parts) < 3:
            raise ValueError("Неверная команда. Используйте /stock_history SYMBOL DAYS")

        Some_currency = command_parts[1].upper()
        num_days = int(command_parts[2])
        end_date = datetime.now()
        start_date = end_date - timedelta(days=1000)
        df = si.get_data(f"{Some_currency}", start_date, end_date).reset_index().iloc[:, :2].rename(
            columns={'index': 'ds', 'open': 'y'})

        df['ds'] = pd.to_datetime(df['ds'])
        df = df[['ds', 'y']].tail(100).reset_index(drop=True)

        model = Prophet(growth='linear', n_changepoints=40)
        model.fit(df)

        future = model.make_future_dataframe(periods=num_days, freq='D')

        forecast = model.predict(future)
        print(forecast)
        predicted_value = forecast[['ds', 'yhat']].tail(num_days)

        plot_title = f"Предсказание цен акции {Some_currency} на последующие {num_days} дней"
        plt.figure(figsize=(10, 6))
        plt.plot(df['ds'].iloc[len(df) - num_days:len(df)] + pd.DateOffset(days=num_days), predicted_value['yhat'],
                 marker='o', linestyle='-')
        plt.title(plot_title)
        plt.xlabel('Дата')
        plt.ylabel('Цена закрытия ($)')
        plt.grid(True)
        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png')
        img_buffer.seek(0)

        await bot.send_photo(message.chat.id, photo=img_buffer)

        plt.close()

    except ValueError as ve:
        # Обрабатываем ошибку неверной команды
        error_message = "Чтобы воспользоваться данной функцией, укажите акцию и количество дней,\n" \
                        f"за которое вас интересует её график предсказаний.\n" \
                        f"Например: <code>/predict_price BTC-USD 7</code>."
        await bot.send_message(message.chat.id, error_message, parse_mode="HTML")

    except Exception as e:
        # Обрабатываем другие исключения (например, ошибки при получении данных)
        error_message = f"Произошла ошибка при вводе.\n" \
                        f"Пожалуйста, укажите акцию и количество дней,\n" \
                        f"за которое вас интересует её график предсказаний.\n" \
                        f"Например: <code>/predict_price BTC-USD 7</code>."
        await bot.send_message(message.chat.id, error_message, parse_mode="HTML")


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
    dp.register_message_handler(get_stock_price, commands=['moment_price'])
    dp.register_message_handler(get_stock_history, commands=['stock_history'])
    dp.register_message_handler(get_stock_predict, commands=['predict_price'])
    dp.register_message_handler(start_monitoring, commands=['start_monitoring'])
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
