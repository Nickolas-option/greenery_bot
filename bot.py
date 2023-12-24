import asyncio
from dateutil.relativedelta import relativedelta
import json
import logging
import os
import datetime
from datetime import timedelta
import numpy as np
import os
import pandas as pd
import time
import yahoo_fin.stock_info as si
import random
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
                endpoint_url=os.environ.get('USER_STORAGE_URL'),
                region_name = 'us-east-1',
                aws_access_key_id = os.environ.get('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
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
    def __init__(self, stock_file_name_constructor, requests_filename,\
                 stock_df_header, first_request_history_days = 1095):
        self.request_id = 0
        
        self.last_request_dict = {}
        
        self.stock_file_name_constructor = stock_file_name_constructor
        
            
        self.requests_filename = requests_filename
        self.stock_df_header = stock_df_header
        self.update_threshold = relativedelta(days=1) # дельта дней
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
                        historical_prices.to_csv(path_or_buf = stock_file_name, header = False, mode = 'a')
                        self.last_request_dict[stock_name] = current_date
                    
                       
                except Exception as e:
                    error_message = f"Произошла ошибка при получении цены акции: {str(e)}"
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

default_parser = Parser(stock_file_name_constructor = history_stock_df_name,\
                        requests_filename = requests_filename,\
                        stock_df_header = stock_df_header)

##############################

async def save_stock_alert(telegram_id, current_datetime, stock_name, current_price, percentage, sign, context):
    dynamodb = boto3.resource('dynamodb', endpoint_url=DYNAMODB_ENDPOINT,
                              region_name='us-east-1',
                              aws_access_key_id=AWS_ACCESS_KEY_ID,
                              aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
    table = dynamodb.Table(DYNAMODB_TABLE_NAME)

    stock_data = {
        'telegram_id': str(telegram_id),
        'current_datetime': current_datetime,
        'stock_name': stock_name,
        'current_price': Decimal(str(current_price)),
        'percentage': Decimal(str(percentage)),
        'sign': sign
    }

    table.put_item(Item=stock_data)

async def start_monitoring(update: Update, context: CallbackContext):
    user_id = update.effective_user.id

    # Get the stock name from the user's message
    stock_name = context.args[0].upper() if context.args else None

    if stock_name:
        # Set default values
        current_price = get_current_price(stock_name)
        percentage = 5.0
        sign = 1  # Positive sign

        # Save stock alert to DynamoDB
        await save_stock_alert(user_id, str(datetime.now()), stock_name, current_price, percentage, sign, context)

        message = f"Monitoring started for {stock_name} with default values."
    else:
        message = "Please provide a valid stock name. Usage: /start_monitoring <stock_name>"

    try:
        await context.bot.send_message(chat_id=user_id, text=message)
    except MessageTextIsEmpty:
        pass

async def get_stock_alerts(telegram_id, context):
    # Retrieve stock alerts from DynamoDB
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
        error_message = "Пожалуйста, укажите тикер акции после команды /moment_price.\n" \
                        f"Например: <code>/moment_price AAPL</code>"
        await bot.send_message(message.chat.id, error_message, parse_mode="HTML")


    except Exception as e:
        # Если произошла ошибка при получении цены акции
        error_message = f"Произошла ошибка при получении цены акции: {str(e)}"
        await bot.send_message(message.chat.id, error_message)
        logging.error(error_message)


async def get_stock_history(message: types.Message):
    try:
        # Получаем символ акции и количество дней из сообщения пользователя
        command_parts = message.text.split()
        if len(command_parts) != 3:
            raise ValueError("Неверная команда. Используйте /stock_history SYMBOL DAYS")

        stock_symbol = command_parts[1].upper()
        num_days = int(command_parts[2])

        # Получаем исторические цены акции за указанное количество дней
        end_date = datetime.now()
        start_date = end_date - relativedelta(days=num_days) # кол-во дней (дельта дней)
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
        error_message = "Пожалуйста, укажите акцию и количество дней, за которое вас интересует её график.\n" \
                        f"Например: <code>/stock_history TSLA 14</code>"
        await bot.send_message(message.chat.id, error_message, parse_mode="HTML")

    except Exception as e:
        # Обрабатываем другие исключения (например, ошибки при получении данных)
        await message.reply(f"Произошла ошибка: {e}")

async def get_stock_predict(message: types.Message):
    def predict(Some_currency):
        Some_currency = Some_currency.upper()
        end_date = datetime.now()
        start_date = end_date - timedelta(days=10)
        df = si.get_data(f"{Some_currency}", start_date, end_date).reset_index().iloc[:, :2].rename(
            columns={'index': 'ds', 'open': 'y'})

        df['ds'] = pd.to_datetime(df['ds'])
        df = df[['ds', 'y']].tail(10).reset_index(drop=True)

        model = Prophet(growth='linear', changepoints=None)
        model.fit(df)

        future = model.make_future_dataframe(periods=1, freq='D')

        forecast = model.predict(future)
        predicted_value = forecast[['ds', 'yhat']].tail(1)

        return float(predicted_value['yhat'])

    try:
        # Получаем символ акции из сообщения пользователя
        command_parts = message.text.split()
        if len(command_parts) != 2:
            raise ValueError("Неверная команда. Используйте /predict_price SYMBOL")

        stock_symbol = command_parts[1].upper()

        # Получаем предсказание цены акции
        predict_price = predict(stock_symbol)

        # Отправляем цену пользователю
        response_text = f"Предсказание стоимости акции {stock_symbol}: ${predict_price:.2f}"
        await bot.send_message(message.chat.id, response_text)

    except ValueError as ve:
        # Обрабатываем ошибку неверной команды
        error_message = "Пожалуйста, укажите акцию, для которой вас интересует предсказание цены.\n" \
                        f"Например: <code>/predict_price GOOGL</code>"
        await bot.send_message(message.chat.id, error_message, parse_mode="HTML")

    except Exception as e:
        # Обрабатываем другие исключения (например, ошибки при получении данных)
        await message.reply(f"Произошла ошибка.")

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
