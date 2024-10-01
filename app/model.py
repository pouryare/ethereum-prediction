import numpy as np
import pandas as pd
from tensorflow import keras
from sklearn.preprocessing import MinMaxScaler
import h5py
from datetime import datetime, timedelta
import os

base = os.getcwd()

# Load the model
model = keras.models.load_model(os.path.join(base, 'ethereum_price_model_full.keras'))

# Load the scaler
scaler = MinMaxScaler()
with h5py.File(os.path.join(base, 'scaler_full.h5'), 'r') as hf:
    scaler.min_ = hf['min'][:]
    scaler.scale_ = hf['scale'][:]
    scaler.data_min_ = scaler.min_
    scaler.data_max_ = scaler.min_ + 1 / scaler.scale_
    scaler.data_range_ = scaler.data_max_ - scaler.data_min_

# Load the latest data
data = pd.read_csv(os.path.join(base, 'ETH_1H.csv'), parse_dates=['Date'], index_col=['Date'])
data = data.sort_index()

window_size = 240  # 10 days of hourly data

def create_steps(to_date):
    last_date = data.index[-1]
    target_date = datetime.strptime(to_date, "%d/%m/%Y")
    delta = target_date - last_date
    steps_in_future = delta.days * 24 + delta.seconds // 3600
    return steps_in_future

def future_predict(steps_in_future):
    last_sequence = scaler.transform(data['Close'].iloc[-window_size:].values.reshape(-1, 1))
    last_real_price = data['Close'].iloc[-1]
    future_predictions = []

    for i in range(steps_in_future):
        next_pred = model.predict(last_sequence.reshape(1, window_size, 1))

        if i == 0:
            scaling_factor = last_real_price / scaler.inverse_transform(next_pred)[0, 0]
            next_pred = scaler.transform(np.array([[last_real_price * 1.001]]))
        else:
            noise = np.random.normal(0, 0.002, next_pred.shape)
            next_pred = next_pred + noise

        future_predictions.append(next_pred[0, 0])
        last_sequence = np.roll(last_sequence, -1)
        last_sequence[-1] = next_pred

    future_predictions = np.array(future_predictions).reshape(-1, 1)
    future_predictions_original = scaler.inverse_transform(future_predictions) * scaling_factor

    return future_predictions_original.flatten()

def get_historical_and_future_data(to_date):
    steps = create_steps(to_date)
    future_prices = future_predict(steps)
    
    historical_prices = data['Close'].values
    future_dates = pd.date_range(start=data.index[-1] + timedelta(hours=1), periods=len(future_prices), freq='H')
    
    return historical_prices, data.index, future_prices, future_dates