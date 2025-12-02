from fastapi import HTTPException
from typing import List, Optional
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import joblib
import os
import logging
from datetime import datetime
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class MarketData(BaseModel):
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float

class MLModel:
    def __init__(self):
        self.model = RandomForestClassifier()
        self.model_path = "ml_model.pkl"
        self.load_model()

    def preprocess_data(self, data: List[MarketData]) -> pd.DataFrame:
        df = pd.DataFrame([d.dict() for d in data])
        df['returns'] = df['close'].pct_change()
        df['volatility'] = df['returns'].rolling(20).std()
        df['rsi'] = self.calculate_rsi(df['close'])
        df.dropna(inplace=True)
        return df

    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def train(self, data: List[MarketData]):
        df = self.preprocess_data(data)
        X = df[['returns', 'volatility', 'rsi']]
        y = np.where(df['returns'].shift(-1) > 0, 1, 0)
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
        self.model.fit(X_train, y_train)
        accuracy = accuracy_score(y_test, self.model.predict(X_test))
        self.save_model()
        return {"accuracy": accuracy}

    def predict(self, data: List[MarketData]) -> dict:
        df = self.preprocess_data(data)
        X = df[['returns', 'volatility', 'rsi']]
        prediction = self.model.predict(X[-1:])[0]
        return {"prediction": "buy" if prediction == 1 else "sell"}

    def save_model(self):
        joblib.dump(self.model, self.model_path)

    def load_model(self):
        if os.path.exists(self.model_path):
            self.model = joblib.load(self.model_path)
