import pandas as pd
import numpy as np
from xgboost import XGBRegressor
from keras.models import Sequential
from keras.layers import LSTM, Dense
from sklearn.model_selection import train_test_split

# df 是包含历史销售、天气和假期信息的 DataFrame
df = pd.read_csv('historical_data.csv')

# 数据准备
X = df[['historical_sales', 'weather', 'holiday']].values
y = df['future_customer_flow'].values

# 划分训练集和测试集
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 训练XGBoost模型
xgb_model = XGBRegressor()
xgb_model.fit(X_train, y_train)

# 预测客流
predicted_flow = xgb_model.predict(X_test)

# LSTM 模型构建
X_lstm = X.reshape((X.shape[0], 1, X.shape[1]))

model = Sequential()
model.add(LSTM(50, return_sequences=True, input_shape=(X_lstm.shape[1], X_lstm.shape[2])))
model.add(LSTM(50))
model.add(Dense(1))
model.compile(optimizer='adam', loss='mean_squared_error')

# 训练LSTM模型
model.fit(X_lstm, y, epochs=50, batch_size=32)