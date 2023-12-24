import asyncio
import aioschedule
import pandas as pd


def display_stranges(user_id, current_price):
    df = pd.read_csv(f"{user_id}.csv")
    for i in range(1, len(df)):
        if df.iloc[i, 1] == 1:
            df2 = pd.read_csv(f"history_{df.iloc[i, 0]}.csv")
            last_row = df2.iloc[-1]
            price = last_row[1]
            if current_price > (price * 1.05):
                print(f"Цена по акции {df.iloc[i, 0]} возросла больше чем на 5%!\n")
            if current_price < (price * 0.95):
                print(f"Цена по акции {df.iloc[i, 0]} упала больше чем на 5%!\n")
            return price


async def scheduler():
    aioschedule.every().day.at("12:00").do(display_stranges)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)

async def on_startup(_):
    asyncio.create_task(scheduler())

dp = Dispatcher(bot)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=False, on_startup=on_startup)
