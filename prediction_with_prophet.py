import pandas as pd
from fbprophet import Prophet
import yahoo_fin.stock_info as si
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

def predict(Some_currency):
    Some_currency = Some_currency.upper()
    end_date = datetime.now()
    start_date = end_date - timedelta(days=10)
    df = si.get_data(f"{Some_currency}", start_date, end_date).reset_index().iloc[:, :2].rename(columns = {'Datetime' : 'ds', 'Open' : 'y'})

    df['ds'] = pd.to_datetime(df['ds'])
    df = df[['ds', 'y']].tail(10).reset_index(drop=True)

    model = Prophet(growth='linear', changepoints=None)
    model.fit(df)

    future = model.make_future_dataframe(periods=1, freq= 60)

    forecast = model.predict(future)
    predicted_value = forecast[['ds', 'yhat']].tail(1)

    predicted_value.to_csv(f'Predict {Some_currency}.csv', index=False)
