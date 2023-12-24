from telegram.ext import Updater, CommandHandler, CallbackContext
import csv
import logging
from telegram import Update

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

updater = Updater(token='YOUR_TOKEN', use_context=True)
dispatcher = updater.dispatcher

currencies = {
    'EUR/RUB': 0,
    'USD/RUB': 0,
    'USD/BTC': 0,
}


def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    filename = f"{user_id}.csv"
    with open(filename, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["EUR/RUB", "USD/RUB", "USD/BTC"])
    update.message.reply_text(f"File for {user_id} is successfully  created.")
    message = "Choose currency pairs:\n\n"
    for currency, value in currencies.items():
        message += f"{currency}: {'✅' if (value == 1) else '❌'}\n"
    context.bot.send_message(chat_id=user_id, text=message)


def select_currency(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    selected_currency = update.message.text.split()[0]

    if selected_currency in currencies:
        currencies[selected_currency] = 1
        message = f"You have chosen {selected_currency}"
    else:
        message = f"Currency pair is not found"

    context.bot.send_message(chat_id=user_id, text=message)


def save_currencies(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    filename = f'{user_id}.csv'
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Currency', 'Selected'])
        for currency, value in currencies.items():
            writer.writerow([currency, value])

    user_id = update.effective_user.id
    context.bot.send_document(chat_id=user_id, document=open(filename, 'rb'))


dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("select", select_currency))
dispatcher.add_handler(CommandHandler("save", save_currencies))

updater.start_polling()
