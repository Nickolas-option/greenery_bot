import pandas as pd
from prophet import Prophet
import yahoo_fin.stock_info as si
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

def predict(Some_currency, num_days):
    Some_currency = Some_currency.upper()
    end_date = datetime.now()
    start_date = end_date - timedelta(days=1000)
    df = si.get_data(f"{Some_currency}", start_date, end_date).reset_index().iloc[:, :2].rename(columns = {'index' : 'ds', 'open' : 'y'})

    df['ds'] = pd.to_datetime(df['ds'])
    df = df[['ds', 'y']].tail(100).reset_index(drop=True)

    model = Prophet(growth='linear', n_changepoints=40)
    model.fit(df)

    future = model.make_future_dataframe(periods=num_days, freq= 'D')

    forecast = model.predict(future)
    print(forecast)
    predicted_value = forecast[['ds', 'yhat']].tail(num_days)

    plot_title = f"Предсказание цен акции {Some_currency} на последующие {num_days} дней"
    plt.figure(figsize=(10, 6))
    plt.plot(df['ds'].iloc[len(df) - num_days:len(df)] + pd.DateOffset(days=10), predicted_value['yhat'], marker='o', linestyle='-')
    plt.title(plot_title)
    plt.xlabel('Дата')
    plt.ylabel('Цена закрытия ($)')
    plt.grid(True)

