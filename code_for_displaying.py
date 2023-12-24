import schedule
import time
import pandas as pd


def job(stock, current_price):
    df = pd.read_csv(f"history_{stock}.csv")
    last_row = df.iloc[-1]
    price = last_row[1]
    if current_price > (price * 1.05):
        print("Цена возросла больше чем на 5%!")
    if current_price < (price * 0.95):
        print("Цена упала!")
    return price


schedule.every().day.at("12:00").do(job)


while True:
    schedule.run_pending()
    time.sleep(1)
