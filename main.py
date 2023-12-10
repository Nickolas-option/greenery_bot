import pandas as pd
from fbprophet import Prophet


df = pd.read_csv('Some_currency.csv').reset_index().rename(columns = {'Datetime' : 'ds', 'Open' : 'y'})

df['ds'] = pd.to_datetime(df['ds'])
df = df[['ds', 'y']].tail(10).reset_index(drop=True)

model = Prophet(growth='linear', changepoints=None)
model.fit(df)

future = model.make_future_dataframe(periods=1, freq= 60)

forecast = model.predict(future)
predicted_value = forecast[['ds', 'yhat']].tail(1)

predicted_value.to_csv('predict.csv', index=False)