import pandas as pd

def get_last_price(csv_file, current_price):
    df = pd.read_csv(csv_file)
    last_row = df.iloc[-1]
    price = last_row[1]
    if current_price > (price * 1.05):
        print("Куда бежишь, э")
    if current_price < (price * 0.95):
        print("Я в лужу упал, и в меня стреляли")
    return price
