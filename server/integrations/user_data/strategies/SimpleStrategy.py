from freqtrade.strategy import IStrategy, IntParameter
from pandas import DataFrame
import talib.abstract as ta
import numpy as np

class SimpleStrategy(IStrategy):
    """
    Simple strategy using RSI for trend following.
    """
    
    # Strategy interface version
    INTERFACE_VERSION = 3

    # Minimal ROI designed for the strategy
    minimal_roi = {
        "0": 0.1
    }

    # Optimal stoploss designed for the strategy
    stoploss = -0.2

    # Trailing stoploss
    trailing_stop = False

    # Timeframe for the strategy
    timeframe = "5m"

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Adds several different TA indicators to the given DataFrame.
        """
        # RSI
        dataframe['rsi'] = ta.RSI(dataframe['close'], timeperiod=14)

        # MACD - handle different return types from ta.MACD (dict or tuple/list)
        macd = ta.MACD(dataframe['close'])
        if isinstance(macd, dict):
            dataframe['macd'] = macd.get('macd')
            dataframe['macdsignal'] = macd.get('macdsignal')
        else:
            # talib may return a tuple/ndarray-like (macd, macdsignal, macdhist)
            try:
                macd_vals, macd_signal, _ = macd
            except Exception:
                # Fallback: coerce to array and slice
                macd_arr = np.asarray(macd)
                macd_vals = macd_arr[0]
                macd_signal = macd_arr[1]
            dataframe['macd'] = macd_vals
            dataframe['macdsignal'] = macd_signal
        
        return dataframe

    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Based on TA indicators, populates the buy signal.
        """
        dataframe.loc[
            (
                (dataframe['rsi'] < 30) &  # Oversold
                (dataframe['macd'] > dataframe['macdsignal'])  # MACD crosses above signal
            ),
            'buy'] = 1

        return dataframe

    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Based on TA indicators, populates the sell signal.
        """
        dataframe.loc[
            (
                (dataframe['rsi'] > 70) &  # Overbought
                (dataframe['macd'] < dataframe['macdsignal'])  # MACD crosses below signal
            ),
            'sell'] = 1
        return dataframe