import pandas as pd
from prophet import Prophet
import yahoo_fin.stock_info as si
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

def predict(message: types.Message):
    try:
      command_parts = message.text.split()
      if len(command_parts) != 3:
          raise ValueError("Неверная команда. Используйте /stock_history SYMBOL DAYS")


      Some_currency = command_parts[1].upper()
      num_days = int(command_parts[2])
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
      plt.plot(df['ds'].iloc[len(df) - num_days:len(df)] + pd.DateOffset(days=num_days), predicted_value['yhat'], marker='o', linestyle='-')
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
        error_message = "Пожалуйста, укажите акцию и количество дней, за которое вас интересует её график.\n" \
                        f"Например: <code>/stock_history TSLA 14</code>"
        await bot.send_message(message.chat.id, error_message, parse_mode="HTML")

    except Exception as e:
        # Обрабатываем другие исключения (например, ошибки при получении данных)
        await message.reply(f"Произошла ошибка: {e}")
      

