"""
Populate Indicator Library
Script to create a library of common technical indicators.
"""

import asyncio
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from ..database import DATABASE_URL
from ..models.indicator import (
    Indicator,
    IndicatorLanguage,
    IndicatorStatus,
    IndicatorVersion,
)
from ..models.user import User
from ..services.indicator_execution_engine import INDICATOR_TEMPLATES

logger = logging.getLogger(__name__)

# Create async database session
engine = create_async_engine(DATABASE_URL)
async_session = async_sessionmaker(engine, expire_on_commit=False)


# Extended indicator library with 30+ common indicators
INDICATOR_LIBRARY = {
    "RSI": {
        "name": "Relative Strength Index (RSI)",
        "description": "Measures the speed and magnitude of price changes. Values above 70 indicate overbought, below 30 oversold.",
        "category": "momentum",
        "tags": "rsi, momentum, oscillator, overbought, oversold",
        "code": INDICATOR_TEMPLATES["rsi"],
        "parameters": {"period": 14},
        "is_free": True,
    },
    "MACD": {
        "name": "Moving Average Convergence Divergence (MACD)",
        "description": "Trend-following momentum indicator showing the relationship between two moving averages.",
        "category": "trend",
        "tags": "macd, trend, momentum, moving average",
        "code": INDICATOR_TEMPLATES["macd"],
        "parameters": {"fast": 12, "slow": 26, "signal": 9},
        "is_free": True,
    },
    "Bollinger Bands": {
        "name": "Bollinger Bands",
        "description": "Volatility bands placed above and below a moving average. Price touching bands may indicate overbought/oversold.",
        "category": "volatility",
        "tags": "bollinger, volatility, bands, overbought, oversold",
        "code": INDICATOR_TEMPLATES["bollinger_bands"],
        "parameters": {"period": 20, "std_dev": 2},
        "is_free": True,
    },
    "SMA": {
        "name": "Simple Moving Average",
        "description": "Average price over a specified period. Used to identify trend direction.",
        "category": "trend",
        "tags": "sma, moving average, trend, simple",
        "code": INDICATOR_TEMPLATES["sma"],
        "parameters": {"period": 20},
        "is_free": True,
    },
    "EMA": {
        "name": "Exponential Moving Average",
        "description": "Weighted moving average that gives more weight to recent prices. More responsive than SMA.",
        "category": "trend",
        "tags": "ema, exponential, moving average, trend",
        "code": INDICATOR_TEMPLATES["ema"],
        "parameters": {"period": 20},
        "is_free": True,
    },
    "Stochastic Oscillator": {
        "name": "Stochastic Oscillator",
        "description": "Momentum indicator comparing closing price to price range over a period.",
        "category": "momentum",
        "tags": "stochastic, momentum, oscillator",
        "code": """
# Stochastic Oscillator
def calculate_stochastic(data, k_period=14, d_period=3):
    low_min = data['low'].rolling(window=k_period).min()
    high_max = data['high'].rolling(window=k_period).max()
    k_percent = 100 * ((data['close'] - low_min) / (high_max - low_min))
    d_percent = k_percent.rolling(window=d_period).mean()
    return {
        'k': k_percent.iloc[-1] if len(k_percent) > 0 else 50.0,
        'd': d_percent.iloc[-1] if len(d_percent) > 0 else 50.0
    }

result = calculate_stochastic(df,
    parameters.get('k_period', 14),
    parameters.get('d_period', 3)
)
output = result
values = [result['k']]
""",
        "parameters": {"k_period": 14, "d_period": 3},
        "is_free": True,
    },
    "ATR": {
        "name": "Average True Range",
        "description": "Measures market volatility by calculating the average of true ranges over a period.",
        "category": "volatility",
        "tags": "atr, volatility, true range",
        "code": """
# Average True Range (ATR)
def calculate_atr(data, period=14):
    high_low = data['high'] - data['low']
    high_close = np.abs(data['high'] - data['close'].shift())
    low_close = np.abs(data['low'] - data['close'].shift())
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = true_range.rolling(window=period).mean()
    return atr.iloc[-1] if len(atr) > 0 else 0.0

values = [calculate_atr(df, parameters.get('period', 14))]
""",
        "parameters": {"period": 14},
        "is_free": True,
    },
    "ADX": {
        "name": "Average Directional Index",
        "description": "Measures trend strength regardless of direction. Values above 25 indicate strong trend.",
        "category": "trend",
        "tags": "adx, trend, strength, directional",
        "code": """
# Average Directional Index (ADX)
def calculate_adx(data, period=14):
    high_diff = data['high'].diff()
    low_diff = -data['low'].diff()
    plus_dm = high_diff.where((high_diff > low_diff) & (high_diff > 0), 0)
    minus_dm = low_diff.where((low_diff > high_diff) & (low_diff > 0), 0)
    tr = calculate_atr(data, period)
    plus_di = 100 * (plus_dm.rolling(period).mean() / tr)
    minus_di = 100 * (minus_dm.rolling(period).mean() / tr)
    dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
    adx = dx.rolling(period).mean()
    return adx.iloc[-1] if len(adx) > 0 else 0.0

def calculate_atr(data, period):
    high_low = data['high'] - data['low']
    high_close = np.abs(data['high'] - data['close'].shift())
    low_close = np.abs(data['low'] - data['close'].shift())
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return true_range.rolling(window=period).mean()

values = [calculate_adx(df, parameters.get('period', 14))]
""",
        "parameters": {"period": 14},
        "is_free": True,
    },
    "OBV": {
        "name": "On-Balance Volume",
        "description": "Cumulative volume indicator that adds volume on up days and subtracts on down days.",
        "category": "volume",
        "tags": "obv, volume, on balance",
        "code": """
# On-Balance Volume (OBV)
def calculate_obv(data):
    obv = (np.sign(data['close'].diff()) * data['volume']).fillna(0).cumsum()
    return obv.iloc[-1] if len(obv) > 0 else 0.0

values = [calculate_obv(df)]
""",
        "parameters": {},
        "is_free": True,
    },
    "Williams %R": {
        "name": "Williams %R",
        "description": "Momentum indicator measuring overbought/oversold levels. Similar to Stochastic but inverted.",
        "category": "momentum",
        "tags": "williams, momentum, oscillator",
        "code": """
# Williams %R
def calculate_williams_r(data, period=14):
    high_max = data['high'].rolling(window=period).max()
    low_min = data['low'].rolling(window=period).min()
    wr = -100 * ((high_max - data['close']) / (high_max - low_min))
    return wr.iloc[-1] if len(wr) > 0 else -50.0

values = [calculate_williams_r(df, parameters.get('period', 14))]
""",
        "parameters": {"period": 14},
        "is_free": True,
    },
    # Additional common indicators (expanding library)
    "CCI": {
        "name": "Commodity Channel Index",
        "description": "Identifies cyclical trends. Values above +100 indicate overbought, below -100 oversold.",
        "category": "momentum",
        "tags": "cci, commodity, channel, momentum",
        "code": """
# Commodity Channel Index (CCI)
def calculate_cci(data, period=20):
    typical_price = (data['high'] + data['low'] + data['close']) / 3
    sma_tp = typical_price.rolling(window=period).mean()
    mean_dev = typical_price.rolling(window=period).apply(lambda x: np.mean(np.abs(x - x.mean())))
    cci = (typical_price - sma_tp) / (0.015 * mean_dev)
    return cci.iloc[-1] if len(cci) > 0 else 0.0

values = [calculate_cci(df, parameters.get('period', 20))]
""",
        "parameters": {"period": 20},
        "is_free": True,
    },
    "MFI": {
        "name": "Money Flow Index",
        "description": "Volume-weighted RSI. Values above 80 indicate overbought, below 20 oversold.",
        "category": "volume",
        "tags": "mfi, money flow, volume, rsi",
        "code": """
# Money Flow Index (MFI)
def calculate_mfi(data, period=14):
    typical_price = (data['high'] + data['low'] + data['close']) / 3
    raw_money_flow = typical_price * data['volume']
    positive_flow = raw_money_flow.where(typical_price > typical_price.shift(), 0).rolling(window=period).sum()
    negative_flow = raw_money_flow.where(typical_price < typical_price.shift(), 0).rolling(window=period).sum()
    mfi = 100 - (100 / (1 + positive_flow / negative_flow))
    return mfi.iloc[-1] if len(mfi) > 0 else 50.0

values = [calculate_mfi(df, parameters.get('period', 14))]
""",
        "parameters": {"period": 14},
        "is_free": True,
    },
    "Ichimoku Cloud": {
        "name": "Ichimoku Cloud",
        "description": "Comprehensive trend indicator showing support/resistance and momentum.",
        "category": "trend",
        "tags": "ichimoku, cloud, trend, support, resistance",
        "code": """
# Ichimoku Cloud
def calculate_ichimoku(data, tenkan=9, kijun=26, senkou_b=52):
    tenkan_high = data['high'].rolling(window=tenkan).max()
    tenkan_low = data['low'].rolling(window=tenkan).min()
    tenkan_sen = (tenkan_high + tenkan_low) / 2
    
    kijun_high = data['high'].rolling(window=kijun).max()
    kijun_low = data['low'].rolling(window=kijun).min()
    kijun_sen = (kijun_high + kijun_low) / 2
    
    senkou_high = data['high'].rolling(window=senkou_b).max()
    senkou_low = data['low'].rolling(window=senkou_b).min()
    senkou_b = (senkou_high + senkou_low) / 2
    
    return {
        'tenkan': tenkan_sen.iloc[-1] if len(tenkan_sen) > 0 else data['close'].iloc[-1],
        'kijun': kijun_sen.iloc[-1] if len(kijun_sen) > 0 else data['close'].iloc[-1],
        'senkou_b': senkou_b.iloc[-1] if len(senkou_b) > 0 else data['close'].iloc[-1]
    }

result = calculate_ichimoku(df,
    parameters.get('tenkan', 9),
    parameters.get('kijun', 26),
    parameters.get('senkou_b', 52)
)
output = result
values = [result['tenkan']]
""",
        "parameters": {"tenkan": 9, "kijun": 26, "senkou_b": 52},
        "is_free": True,
    },
    "Parabolic SAR": {
        "name": "Parabolic SAR",
        "description": "Trend-following indicator that provides entry and exit points.",
        "category": "trend",
        "tags": "parabolic, sar, stop and reverse, trend",
        "code": """
# Parabolic SAR (simplified)
def calculate_parabolic_sar(data, af=0.02, max_af=0.2):
    # Simplified implementation
    high = data['high'].iloc[-1]
    low = data['low'].iloc[-1]
    close = data['close'].iloc[-1]
    # Basic SAR calculation
    sar = low if close > high else high
    return sar

values = [calculate_parabolic_sar(df,
    parameters.get('af', 0.02),
    parameters.get('max_af', 0.2)
)]
""",
        "parameters": {"af": 0.02, "max_af": 0.2},
        "is_free": True,
    },
    # Additional indicators to expand library
    "WMA": {
        "name": "Weighted Moving Average",
        "description": "Moving average that gives more weight to recent prices.",
        "category": "trend",
        "tags": "wma, weighted, moving average, trend",
        "code": """
# Weighted Moving Average (WMA)
def calculate_wma(data, period=20):
    weights = np.arange(1, period + 1)
    wma = data['close'].rolling(window=period).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)
    return wma.iloc[-1] if len(wma) > 0 else data['close'].iloc[-1]

values = [calculate_wma(df, parameters.get('period', 20))]
""",
        "parameters": {"period": 20},
        "is_free": True,
    },
    "VWAP": {
        "name": "Volume Weighted Average Price",
        "description": "Average price weighted by volume. Important intraday indicator.",
        "category": "volume",
        "tags": "vwap, volume, weighted, average price",
        "code": """
# Volume Weighted Average Price (VWAP)
def calculate_vwap(data):
    typical_price = (data['high'] + data['low'] + data['close']) / 3
    vwap = (typical_price * data['volume']).cumsum() / data['volume'].cumsum()
    return vwap.iloc[-1] if len(vwap) > 0 else data['close'].iloc[-1]

values = [calculate_vwap(df)]
""",
        "parameters": {},
        "is_free": True,
    },
    "ROC": {
        "name": "Rate of Change",
        "description": "Momentum oscillator measuring percentage change in price over time.",
        "category": "momentum",
        "tags": "roc, rate of change, momentum, oscillator",
        "code": """
# Rate of Change (ROC)
def calculate_roc(data, period=12):
    roc = ((data['close'] - data['close'].shift(period)) / data['close'].shift(period)) * 100
    return roc.iloc[-1] if len(roc) > 0 else 0.0

values = [calculate_roc(df, parameters.get('period', 12))]
""",
        "parameters": {"period": 12},
        "is_free": True,
    },
    "Momentum": {
        "name": "Momentum",
        "description": "Measures the rate of change in price over a specified period.",
        "category": "momentum",
        "tags": "momentum, rate of change, oscillator",
        "code": """
# Momentum
def calculate_momentum(data, period=10):
    momentum = data['close'] - data['close'].shift(period)
    return momentum.iloc[-1] if len(momentum) > 0 else 0.0

values = [calculate_momentum(df, parameters.get('period', 10))]
""",
        "parameters": {"period": 10},
        "is_free": True,
    },
    "TRIX": {
        "name": "TRIX",
        "description": "Triple exponential moving average oscillator showing rate of change.",
        "category": "momentum",
        "tags": "trix, triple ema, momentum, oscillator",
        "code": """
# TRIX
def calculate_trix(data, period=14):
    ema1 = data['close'].ewm(span=period, adjust=False).mean()
    ema2 = ema1.ewm(span=period, adjust=False).mean()
    ema3 = ema2.ewm(span=period, adjust=False).mean()
    trix = ((ema3 - ema3.shift(1)) / ema3.shift(1)) * 100
    return trix.iloc[-1] if len(trix) > 0 else 0.0

values = [calculate_trix(df, parameters.get('period', 14))]
""",
        "parameters": {"period": 14},
        "is_free": True,
    },
    "Ultimate Oscillator": {
        "name": "Ultimate Oscillator",
        "description": "Momentum oscillator using weighted average of three different timeframes.",
        "category": "momentum",
        "tags": "ultimate oscillator, momentum, weighted",
        "code": """
# Ultimate Oscillator
def calculate_ultimate_oscillator(data, short=7, medium=14, long=28):
    bp = data['close'] - pd.concat([data['low'], data['close'].shift()], axis=1).min(axis=1)
    tr = pd.concat([data['high'] - data['low'], 
                    abs(data['high'] - data['close'].shift()),
                    abs(data['low'] - data['close'].shift())], axis=1).max(axis=1)
    avg7 = bp.rolling(short).sum() / tr.rolling(short).sum()
    avg14 = bp.rolling(medium).sum() / tr.rolling(medium).sum()
    avg28 = bp.rolling(long).sum() / tr.rolling(long).sum()
    uo = 100 * ((4 * avg7) + (2 * avg14) + avg28) / (4 + 2 + 1)
    return uo.iloc[-1] if len(uo) > 0 else 50.0

values = [calculate_ultimate_oscillator(df,
    parameters.get('short', 7),
    parameters.get('medium', 14),
    parameters.get('long', 28)
)]
""",
        "parameters": {"short": 7, "medium": 14, "long": 28},
        "is_free": True,
    },
    "Aroon": {
        "name": "Aroon",
        "description": "Identifies trend changes and strength. Consists of Aroon Up and Aroon Down.",
        "category": "trend",
        "tags": "aroon, trend, strength",
        "code": """
# Aroon
def calculate_aroon(data, period=14):
    aroon_up = ((period - data['high'].rolling(period).apply(lambda x: period - 1 - x.argmax(), raw=True)) / period) * 100
    aroon_down = ((period - data['low'].rolling(period).apply(lambda x: period - 1 - x.argmin(), raw=True)) / period) * 100
    return {
        'aroon_up': aroon_up.iloc[-1] if len(aroon_up) > 0 else 50.0,
        'aroon_down': aroon_down.iloc[-1] if len(aroon_down) > 0 else 50.0
    }

result = calculate_aroon(df, parameters.get('period', 14))
output = result
values = [result['aroon_up']]
""",
        "parameters": {"period": 14},
        "is_free": True,
    },
    "Balance of Power": {
        "name": "Balance of Power",
        "description": "Measures the strength of buying vs selling pressure.",
        "category": "volume",
        "tags": "balance of power, volume, buying pressure, selling pressure",
        "code": """
# Balance of Power (BOP)
def calculate_bop(data):
    bop = (data['close'] - data['open']) / (data['high'] - data['low'])
    bop = bop.replace([np.inf, -np.inf], 0).fillna(0)
    return bop.iloc[-1] if len(bop) > 0 else 0.0

values = [calculate_bop(df)]
""",
        "parameters": {},
        "is_free": True,
    },
    "Chaikin Money Flow": {
        "name": "Chaikin Money Flow",
        "description": "Volume-weighted average of accumulation and distribution over a period.",
        "category": "volume",
        "tags": "chaikin, money flow, volume, accumulation",
        "code": """
# Chaikin Money Flow (CMF)
def calculate_cmf(data, period=20):
    mfv = ((data['close'] - data['low']) - (data['high'] - data['close'])) / (data['high'] - data['low'])
    mfv = mfv * data['volume']
    cmf = mfv.rolling(period).sum() / data['volume'].rolling(period).sum()
    return cmf.iloc[-1] if len(cmf) > 0 else 0.0

values = [calculate_cmf(df, parameters.get('period', 20))]
""",
        "parameters": {"period": 20},
        "is_free": True,
    },
    "Donchian Channels": {
        "name": "Donchian Channels",
        "description": "Volatility indicator showing highest high and lowest low over a period.",
        "category": "volatility",
        "tags": "donchian, channels, volatility, breakout",
        "code": """
# Donchian Channels
def calculate_donchian(data, period=20):
    upper = data['high'].rolling(window=period).max()
    lower = data['low'].rolling(window=period).min()
    middle = (upper + lower) / 2
    return {
        'upper': upper.iloc[-1] if len(upper) > 0 else data['close'].iloc[-1],
        'middle': middle.iloc[-1] if len(middle) > 0 else data['close'].iloc[-1],
        'lower': lower.iloc[-1] if len(lower) > 0 else data['close'].iloc[-1]
    }

result = calculate_donchian(df, parameters.get('period', 20))
output = result
values = [result['middle']]
""",
        "parameters": {"period": 20},
        "is_free": True,
    },
    "Keltner Channels": {
        "name": "Keltner Channels",
        "description": "Volatility bands based on EMA and ATR. Similar to Bollinger Bands.",
        "category": "volatility",
        "tags": "keltner, channels, volatility, ema, atr",
        "code": """
# Keltner Channels
def calculate_keltner(data, period=20, multiplier=2.0):
    ema = data['close'].ewm(span=period, adjust=False).mean()
    atr = calculate_atr(data, period)
    upper = ema + (multiplier * atr)
    lower = ema - (multiplier * atr)
    return {
        'upper': upper.iloc[-1] if len(upper) > 0 else data['close'].iloc[-1],
        'middle': ema.iloc[-1] if len(ema) > 0 else data['close'].iloc[-1],
        'lower': lower.iloc[-1] if len(lower) > 0 else data['close'].iloc[-1]
    }

def calculate_atr(data, period):
    high_low = data['high'] - data['low']
    high_close = np.abs(data['high'] - data['close'].shift())
    low_close = np.abs(data['low'] - data['close'].shift())
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return true_range.rolling(window=period).mean()

result = calculate_keltner(df,
    parameters.get('period', 20),
    parameters.get('multiplier', 2.0)
)
output = result
values = [result['middle']]
""",
        "parameters": {"period": 20, "multiplier": 2.0},
        "is_free": True,
    },
    "Standard Deviation": {
        "name": "Standard Deviation",
        "description": "Measures price volatility as standard deviation from moving average.",
        "category": "volatility",
        "tags": "standard deviation, volatility, std",
        "code": """
# Standard Deviation
def calculate_std(data, period=20):
    sma = data['close'].rolling(window=period).mean()
    std = data['close'].rolling(window=period).std()
    return {
        'std': std.iloc[-1] if len(std) > 0 else 0.0,
        'mean': sma.iloc[-1] if len(sma) > 0 else data['close'].iloc[-1]
    }

result = calculate_std(df, parameters.get('period', 20))
output = result
values = [result['std']]
""",
        "parameters": {"period": 20},
        "is_free": True,
    },
    "Price Channels": {
        "name": "Price Channels",
        "description": "Upper and lower bounds based on highest high and lowest low.",
        "category": "volatility",
        "tags": "price channels, volatility, support, resistance",
        "code": """
# Price Channels
def calculate_price_channels(data, period=20):
    upper = data['high'].rolling(window=period).max()
    lower = data['low'].rolling(window=period).min()
    return {
        'upper': upper.iloc[-1] if len(upper) > 0 else data['close'].iloc[-1],
        'lower': lower.iloc[-1] if len(lower) > 0 else data['close'].iloc[-1]
    }

result = calculate_price_channels(df, parameters.get('period', 20))
output = result
values = [(result['upper'] + result['lower']) / 2]
""",
        "parameters": {"period": 20},
        "is_free": True,
    },
    "Z-Score": {
        "name": "Z-Score",
        "description": "Measures how many standard deviations a price is from the mean.",
        "category": "volatility",
        "tags": "z-score, standard deviation, mean reversion",
        "code": """
# Z-Score
def calculate_zscore(data, period=20):
    sma = data['close'].rolling(window=period).mean()
    std = data['close'].rolling(window=period).std()
    zscore = (data['close'] - sma) / std
    return zscore.iloc[-1] if len(zscore) > 0 else 0.0

values = [calculate_zscore(df, parameters.get('period', 20))]
""",
        "parameters": {"period": 20},
        "is_free": True,
    },
    "Elder Ray Index": {
        "name": "Elder Ray Index",
        "description": "Measures buying and selling pressure using EMA and price extremes.",
        "category": "momentum",
        "tags": "elder ray, buying pressure, selling pressure, ema",
        "code": """
# Elder Ray Index
def calculate_elder_ray(data, period=13):
    ema = data['close'].ewm(span=period, adjust=False).mean()
    bull_power = data['high'] - ema
    bear_power = data['low'] - ema
    return {
        'bull_power': bull_power.iloc[-1] if len(bull_power) > 0 else 0.0,
        'bear_power': bear_power.iloc[-1] if len(bear_power) > 0 else 0.0
    }

result = calculate_elder_ray(df, parameters.get('period', 13))
output = result
values = [result['bull_power']]
""",
        "parameters": {"period": 13},
        "is_free": True,
    },
    "Force Index": {
        "name": "Force Index",
        "description": "Combines price and volume to measure buying and selling pressure.",
        "category": "volume",
        "tags": "force index, volume, price, momentum",
        "code": """
# Force Index
def calculate_force_index(data, period=13):
    price_change = data['close'].diff()
    force = price_change * data['volume']
    force_index = force.ewm(span=period, adjust=False).mean()
    return force_index.iloc[-1] if len(force_index) > 0 else 0.0

values = [calculate_force_index(df, parameters.get('period', 13))]
""",
        "parameters": {"period": 13},
        "is_free": True,
    },
    "Ease of Movement": {
        "name": "Ease of Movement",
        "description": "Measures the relationship between price change and volume.",
        "category": "volume",
        "tags": "ease of movement, volume, price change",
        "code": """
# Ease of Movement (EOM)
def calculate_eom(data, period=14):
    distance = ((data['high'] + data['low']) / 2) - ((data['high'].shift() + data['low'].shift()) / 2)
    box_ratio = data['volume'] / (data['high'] - data['low'])
    eom = distance / box_ratio
    eom_sma = eom.rolling(window=period).mean()
    return eom_sma.iloc[-1] if len(eom_sma) > 0 else 0.0

values = [calculate_eom(df, parameters.get('period', 14))]
""",
        "parameters": {"period": 14},
        "is_free": True,
    },
    "Mass Index": {
        "name": "Mass Index",
        "description": "Identifies trend reversals by measuring the range between high and low prices.",
        "category": "volatility",
        "tags": "mass index, volatility, trend reversal",
        "code": """
# Mass Index
def calculate_mass_index(data, period=25, sum_period=9):
    high_low = data['high'] - data['low']
    ema = high_low.ewm(span=period, adjust=False).mean()
    ema_ema = ema.ewm(span=period, adjust=False).mean()
    ratio = ema / ema_ema
    mass_index = ratio.rolling(window=sum_period).sum()
    return mass_index.iloc[-1] if len(mass_index) > 0 else 0.0

values = [calculate_mass_index(df,
    parameters.get('period', 25),
    parameters.get('sum_period', 9)
)]
""",
        "parameters": {"period": 25, "sum_period": 9},
        "is_free": True,
    },
    "Vortex Indicator": {
        "name": "Vortex Indicator",
        "description": "Identifies trend direction using positive and negative trend movement.",
        "category": "trend",
        "tags": "vortex, trend, direction",
        "code": """
# Vortex Indicator
def calculate_vortex(data, period=14):
    tr = pd.concat([data['high'] - data['low'],
                    abs(data['high'] - data['close'].shift()),
                    abs(data['low'] - data['close'].shift())], axis=1).max(axis=1)
    vm_plus = abs(data['high'] - data['low'].shift())
    vm_minus = abs(data['low'] - data['high'].shift())
    vi_plus = vm_plus.rolling(window=period).sum() / tr.rolling(window=period).sum()
    vi_minus = vm_minus.rolling(window=period).sum() / tr.rolling(window=period).sum()
    return {
        'vi_plus': vi_plus.iloc[-1] if len(vi_plus) > 0 else 0.0,
        'vi_minus': vi_minus.iloc[-1] if len(vi_minus) > 0 else 0.0
    }

result = calculate_vortex(df, parameters.get('period', 14))
output = result
values = [result['vi_plus']]
""",
        "parameters": {"period": 14},
        "is_free": True,
    },
    "Negative Volume Index": {
        "name": "Negative Volume Index",
        "description": "Tracks price changes on days with decreased volume.",
        "category": "volume",
        "tags": "nvi, negative volume, volume, price",
        "code": """
# Negative Volume Index (NVI)
def calculate_nvi(data):
    price_change = data['close'].pct_change()
    nvi = 1000  # Starting value
    for i in range(1, len(data)):
        if data['volume'].iloc[i] < data['volume'].iloc[i-1]:
            nvi = nvi * (1 + price_change.iloc[i])
    return nvi

values = [calculate_nvi(df)]
""",
        "parameters": {},
        "is_free": True,
    },
    "Positive Volume Index": {
        "name": "Positive Volume Index",
        "description": "Tracks price changes on days with increased volume.",
        "category": "volume",
        "tags": "pvi, positive volume, volume, price",
        "code": """
# Positive Volume Index (PVI)
def calculate_pvi(data):
    price_change = data['close'].pct_change()
    pvi = 1000  # Starting value
    for i in range(1, len(data)):
        if data['volume'].iloc[i] > data['volume'].iloc[i-1]:
            pvi = pvi * (1 + price_change.iloc[i])
    return pvi

values = [calculate_pvi(df)]
""",
        "parameters": {},
        "is_free": True,
    },
    # Additional advanced indicators (expanding to 70+)
    "DMI": {
        "name": "Directional Movement Index",
        "description": "Measures trend direction and strength. Components: +DI, -DI, ADX.",
        "category": "trend",
        "tags": "dmi, directional movement, trend, adx",
        "code": """
# Directional Movement Index (DMI)
def calculate_dmi(data, period=14):
    high_diff = data['high'].diff()
    low_diff = -data['low'].diff()
    plus_dm = high_diff.where((high_diff > low_diff) & (high_diff > 0), 0)
    minus_dm = low_diff.where((low_diff > high_diff) & (low_diff > 0), 0)
    tr = calculate_atr(data, period)
    plus_di = 100 * (plus_dm.rolling(period).mean() / tr)
    minus_di = 100 * (minus_dm.rolling(period).mean() / tr)
    return {
        'plus_di': plus_di.iloc[-1] if len(plus_di) > 0 else 0.0,
        'minus_di': minus_di.iloc[-1] if len(minus_di) > 0 else 0.0
    }

def calculate_atr(data, period):
    high_low = data['high'] - data['low']
    high_close = np.abs(data['high'] - data['close'].shift())
    low_close = np.abs(data['low'] - data['close'].shift())
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return true_range.rolling(window=period).mean()

result = calculate_dmi(df, parameters.get('period', 14))
output = result
values = [result['plus_di']]
""",
        "parameters": {"period": 14},
        "is_free": True,
    },
    "Awesome Oscillator": {
        "name": "Awesome Oscillator",
        "description": "Measures market momentum using the difference between 5 and 34 period SMAs.",
        "category": "momentum",
        "tags": "awesome oscillator, momentum, sma",
        "code": """
# Awesome Oscillator
def calculate_awesome_oscillator(data):
    sma_5 = data['close'].rolling(window=5).mean()
    sma_34 = data['close'].rolling(window=34).mean()
    ao = sma_5 - sma_34
    return ao.iloc[-1] if len(ao) > 0 else 0.0

values = [calculate_awesome_oscillator(df)]
""",
        "parameters": {},
        "is_free": True,
    },
    "Accumulation/Distribution Line": {
        "name": "Accumulation/Distribution Line",
        "description": "Volume-based indicator showing money flow into or out of a security.",
        "category": "volume",
        "tags": "accumulation, distribution, volume, money flow",
        "code": """
# Accumulation/Distribution Line (A/D)
def calculate_ad_line(data):
    clv = ((data['close'] - data['low']) - (data['high'] - data['close'])) / (data['high'] - data['low'])
    clv = clv.replace([np.inf, -np.inf], 0).fillna(0)
    ad = (clv * data['volume']).cumsum()
    return ad.iloc[-1] if len(ad) > 0 else 0.0

values = [calculate_ad_line(df)]
""",
        "parameters": {},
        "is_free": True,
    },
    "Commodity Selection Index": {
        "name": "Commodity Selection Index",
        "description": "Momentum indicator measuring rate of change adjusted for volatility.",
        "category": "momentum",
        "tags": "csi, commodity selection, momentum, volatility",
        "code": """
# Commodity Selection Index (CSI)
def calculate_csi(data, period=14):
    roc = ((data['close'] - data['close'].shift(period)) / data['close'].shift(period)) * 100
    atr = calculate_atr(data, period)
    csi = (roc / atr) * 100
    return csi.iloc[-1] if len(csi) > 0 else 0.0

def calculate_atr(data, period):
    high_low = data['high'] - data['low']
    high_close = np.abs(data['high'] - data['close'].shift())
    low_close = np.abs(data['low'] - data['close'].shift())
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return true_range.rolling(window=period).mean()

values = [calculate_csi(df, parameters.get('period', 14))]
""",
        "parameters": {"period": 14},
        "is_free": True,
    },
    "Detrended Price Oscillator": {
        "name": "Detrended Price Oscillator",
        "description": "Removes trend from price to identify cycles and overbought/oversold conditions.",
        "category": "momentum",
        "tags": "dpo, detrended, oscillator, cycles",
        "code": """
# Detrended Price Oscillator (DPO)
def calculate_dpo(data, period=20):
    sma = data['close'].rolling(window=period).mean()
    dpo = data['close'] - sma.shift(int(period / 2 + 1))
    return dpo.iloc[-1] if len(dpo) > 0 else 0.0

values = [calculate_dpo(df, parameters.get('period', 20))]
""",
        "parameters": {"period": 20},
        "is_free": True,
    },
    "Know Sure Thing": {
        "name": "Know Sure Thing",
        "description": "Momentum oscillator using rate of change from multiple timeframes.",
        "category": "momentum",
        "tags": "kst, know sure thing, momentum, roc",
        "code": """
# Know Sure Thing (KST)
def calculate_kst(data):
    roc1 = ((data['close'] - data['close'].shift(10)) / data['close'].shift(10)) * 100
    roc2 = ((data['close'] - data['close'].shift(15)) / data['close'].shift(15)) * 100
    roc3 = ((data['close'] - data['close'].shift(20)) / data['close'].shift(20)) * 100
    roc4 = ((data['close'] - data['close'].shift(30)) / data['close'].shift(30)) * 100
    sma1 = roc1.rolling(10).mean()
    sma2 = roc2.rolling(10).mean()
    sma3 = roc3.rolling(10).mean()
    sma4 = roc4.rolling(15).mean()
    kst = (sma1 * 1) + (sma2 * 2) + (sma3 * 3) + (sma4 * 4)
    return kst.iloc[-1] if len(kst) > 0 else 0.0

values = [calculate_kst(df)]
""",
        "parameters": {},
        "is_free": True,
    },
    "Percentage Price Oscillator": {
        "name": "Percentage Price Oscillator",
        "description": "Momentum indicator showing the relationship between two EMAs as a percentage.",
        "category": "momentum",
        "tags": "ppo, percentage price oscillator, momentum, ema",
        "code": """
# Percentage Price Oscillator (PPO)
def calculate_ppo(data, fast=12, slow=26):
    ema_fast = data['close'].ewm(span=fast, adjust=False).mean()
    ema_slow = data['close'].ewm(span=slow, adjust=False).mean()
    ppo = ((ema_fast - ema_slow) / ema_slow) * 100
    return ppo.iloc[-1] if len(ppo) > 0 else 0.0

values = [calculate_ppo(df,
    parameters.get('fast', 12),
    parameters.get('slow', 26)
)]
""",
        "parameters": {"fast": 12, "slow": 26},
        "is_free": True,
    },
    "Price Oscillator": {
        "name": "Price Oscillator",
        "description": "Difference between two moving averages as a percentage of the longer average.",
        "category": "momentum",
        "tags": "price oscillator, momentum, moving average",
        "code": """
# Price Oscillator
def calculate_price_oscillator(data, fast=12, slow=26):
    sma_fast = data['close'].rolling(window=fast).mean()
    sma_slow = data['close'].rolling(window=slow).mean()
    po = ((sma_fast - sma_slow) / sma_slow) * 100
    return po.iloc[-1] if len(po) > 0 else 0.0

values = [calculate_price_oscillator(df,
    parameters.get('fast', 12),
    parameters.get('slow', 26)
)]
""",
        "parameters": {"fast": 12, "slow": 26},
        "is_free": True,
    },
    "Relative Vigor Index": {
        "name": "Relative Vigor Index",
        "description": "Measures the strength of a trend by comparing closing and opening prices.",
        "category": "momentum",
        "tags": "rvi, relative vigor index, momentum, trend",
        "code": """
# Relative Vigor Index (RVI)
def calculate_rvi(data, period=14):
    numerator = ((data['close'] - data['open']) + 2 * (data['close'].shift() - data['open'].shift()) + 2 * (data['close'].shift(2) - data['open'].shift(2)) + (data['close'].shift(3) - data['open'].shift(3))) / 6
    denominator = ((data['high'] - data['low']) + 2 * (data['high'].shift() - data['low'].shift()) + 2 * (data['high'].shift(2) - data['low'].shift(2)) + (data['high'].shift(3) - data['low'].shift(3))) / 6
    rvi = (numerator.rolling(period).mean() / denominator.rolling(period).mean()) * 100
    return rvi.iloc[-1] if len(rvi) > 0 else 50.0

values = [calculate_rvi(df, parameters.get('period', 14))]
""",
        "parameters": {"period": 14},
        "is_free": True,
    },
    "True Strength Index": {
        "name": "True Strength Index",
        "description": "Momentum oscillator using double-smoothed price changes.",
        "category": "momentum",
        "tags": "tsi, true strength index, momentum, oscillator",
        "code": """
# True Strength Index (TSI)
def calculate_tsi(data, r=25, s=13):
    price_change = data['close'].diff()
    smoothed_pc = price_change.ewm(span=r, adjust=False).mean().ewm(span=s, adjust=False).mean()
    smoothed_apc = price_change.abs().ewm(span=r, adjust=False).mean().ewm(span=s, adjust=False).mean()
    tsi = (smoothed_pc / smoothed_apc) * 100
    return tsi.iloc[-1] if len(tsi) > 0 else 0.0

values = [calculate_tsi(df,
    parameters.get('r', 25),
    parameters.get('s', 13)
)]
""",
        "parameters": {"r": 25, "s": 13},
        "is_free": True,
    },
    "Ultimate Oscillator": {
        "name": "Ultimate Oscillator",
        "description": "Momentum oscillator using weighted average of three different timeframes.",
        "category": "momentum",
        "tags": "ultimate oscillator, momentum, weighted",
        "code": """
# Ultimate Oscillator
def calculate_ultimate_oscillator(data, short=7, medium=14, long=28):
    bp = data['close'] - pd.concat([data['low'], data['close'].shift()], axis=1).min(axis=1)
    tr = pd.concat([data['high'] - data['low'], 
                    abs(data['high'] - data['close'].shift()),
                    abs(data['low'] - data['close'].shift())], axis=1).max(axis=1)
    avg7 = bp.rolling(short).sum() / tr.rolling(short).sum()
    avg14 = bp.rolling(medium).sum() / tr.rolling(medium).sum()
    avg28 = bp.rolling(long).sum() / tr.rolling(long).sum()
    uo = 100 * ((4 * avg7) + (2 * avg14) + avg28) / (4 + 2 + 1)
    return uo.iloc[-1] if len(uo) > 0 else 50.0

values = [calculate_ultimate_oscillator(df,
    parameters.get('short', 7),
    parameters.get('medium', 14),
    parameters.get('long', 28)
)]
""",
        "parameters": {"short": 7, "medium": 14, "long": 28},
        "is_free": True,
    },
    "Volume Oscillator": {
        "name": "Volume Oscillator",
        "description": "Measures the difference between two volume moving averages.",
        "category": "volume",
        "tags": "volume oscillator, volume, moving average",
        "code": """
# Volume Oscillator
def calculate_volume_oscillator(data, fast=5, slow=10):
    vo = ((data['volume'].rolling(fast).mean() - data['volume'].rolling(slow).mean()) / data['volume'].rolling(slow).mean()) * 100
    return vo.iloc[-1] if len(vo) > 0 else 0.0

values = [calculate_volume_oscillator(df,
    parameters.get('fast', 5),
    parameters.get('slow', 10)
)]
""",
        "parameters": {"fast": 5, "slow": 10},
        "is_free": True,
    },
    "Volume Rate of Change": {
        "name": "Volume Rate of Change",
        "description": "Measures the rate of change in volume over a specified period.",
        "category": "volume",
        "tags": "volume roc, volume, rate of change",
        "code": """
# Volume Rate of Change
def calculate_volume_roc(data, period=12):
    vroc = ((data['volume'] - data['volume'].shift(period)) / data['volume'].shift(period)) * 100
    return vroc.iloc[-1] if len(vroc) > 0 else 0.0

values = [calculate_volume_roc(df, parameters.get('period', 12))]
""",
        "parameters": {"period": 12},
        "is_free": True,
    },
    "Price Rate of Change": {
        "name": "Price Rate of Change",
        "description": "Measures the percentage change in price over a specified period.",
        "category": "momentum",
        "tags": "price roc, momentum, rate of change",
        "code": """
# Price Rate of Change
def calculate_price_roc(data, period=12):
    proc = ((data['close'] - data['close'].shift(period)) / data['close'].shift(period)) * 100
    return proc.iloc[-1] if len(proc) > 0 else 0.0

values = [calculate_price_roc(df, parameters.get('period', 12))]
""",
        "parameters": {"period": 12},
        "is_free": True,
    },
    "Typical Price": {
        "name": "Typical Price",
        "description": "Average of high, low, and close prices. Used as a baseline for other indicators.",
        "category": "trend",
        "tags": "typical price, baseline, average",
        "code": """
# Typical Price
def calculate_typical_price(data):
    tp = (data['high'] + data['low'] + data['close']) / 3
    return tp.iloc[-1] if len(tp) > 0 else data['close'].iloc[-1]

values = [calculate_typical_price(df)]
""",
        "parameters": {},
        "is_free": True,
    },
    "Weighted Close": {
        "name": "Weighted Close",
        "description": "Weighted average giving more importance to the closing price.",
        "category": "trend",
        "tags": "weighted close, average, price",
        "code": """
# Weighted Close
def calculate_weighted_close(data):
    wc = (data['high'] + data['low'] + (2 * data['close'])) / 4
    return wc.iloc[-1] if len(wc) > 0 else data['close'].iloc[-1]

values = [calculate_weighted_close(df)]
""",
        "parameters": {},
        "is_free": True,
    },
    "Median Price": {
        "name": "Median Price",
        "description": "Average of high and low prices.",
        "category": "trend",
        "tags": "median price, average",
        "code": """
# Median Price
def calculate_median_price(data):
    mp = (data['high'] + data['low']) / 2
    return mp.iloc[-1] if len(mp) > 0 else data['close'].iloc[-1]

values = [calculate_median_price(df)]
""",
        "parameters": {},
        "is_free": True,
    },
    "Hull Moving Average": {
        "name": "Hull Moving Average",
        "description": "Weighted moving average that reduces lag while maintaining smoothness.",
        "category": "trend",
        "tags": "hull ma, hma, moving average, trend",
        "code": """
# Hull Moving Average (HMA)
def calculate_hma(data, period=20):
    wma_half = data['close'].rolling(window=int(period/2)).apply(lambda x: np.dot(x, np.arange(1, len(x)+1)) / np.arange(1, len(x)+1).sum(), raw=True)
    wma_full = data['close'].rolling(window=period).apply(lambda x: np.dot(x, np.arange(1, len(x)+1)) / np.arange(1, len(x)+1).sum(), raw=True)
    hma = (2 * wma_half - wma_full).rolling(window=int(np.sqrt(period))).apply(lambda x: np.dot(x, np.arange(1, len(x)+1)) / np.arange(1, len(x)+1).sum(), raw=True)
    return hma.iloc[-1] if len(hma) > 0 else data['close'].iloc[-1]

values = [calculate_hma(df, parameters.get('period', 20))]
""",
        "parameters": {"period": 20},
        "is_free": True,
    },
    "Kaufman Adaptive Moving Average": {
        "name": "Kaufman Adaptive Moving Average",
        "description": "Adaptive moving average that adjusts to market volatility.",
        "category": "trend",
        "tags": "kama, kaufman, adaptive, moving average",
        "code": """
# Kaufman Adaptive Moving Average (KAMA)
def calculate_kama(data, period=10, fast=2, slow=30):
    change = abs(data['close'] - data['close'].shift(period))
    volatility = data['close'].diff().abs().rolling(period).sum()
    er = change / volatility
    sc = (er * (2/(fast+1) - 2/(slow+1)) + 2/(slow+1)) ** 2
    kama = data['close'].copy()
    for i in range(period, len(data)):
        kama.iloc[i] = kama.iloc[i-1] + sc.iloc[i] * (data['close'].iloc[i] - kama.iloc[i-1])
    return kama.iloc[-1] if len(kama) > 0 else data['close'].iloc[-1]

values = [calculate_kama(df,
    parameters.get('period', 10),
    parameters.get('fast', 2),
    parameters.get('slow', 30)
)]
""",
        "parameters": {"period": 10, "fast": 2, "slow": 30},
        "is_free": True,
    },
    "Zero Lag Exponential Moving Average": {
        "name": "Zero Lag Exponential Moving Average",
        "description": "EMA variant designed to eliminate lag.",
        "category": "trend",
        "tags": "zlema, zero lag, ema, trend",
        "code": """
# Zero Lag Exponential Moving Average (ZLEMA)
def calculate_zlema(data, period=20):
    lag = (period - 1) / 2
    ema_data = data['close'] + (data['close'] - data['close'].shift(int(lag)))
    zlema = ema_data.ewm(span=period, adjust=False).mean()
    return zlema.iloc[-1] if len(zlema) > 0 else data['close'].iloc[-1]

values = [calculate_zlema(df, parameters.get('period', 20))]
""",
        "parameters": {"period": 20},
        "is_free": True,
    },
    "Triple Exponential Moving Average": {
        "name": "Triple Exponential Moving Average",
        "description": "Triple-smoothed EMA that reduces noise and lag.",
        "category": "trend",
        "tags": "tema, triple ema, moving average, trend",
        "code": """
# Triple Exponential Moving Average (TEMA)
def calculate_tema(data, period=20):
    ema1 = data['close'].ewm(span=period, adjust=False).mean()
    ema2 = ema1.ewm(span=period, adjust=False).mean()
    ema3 = ema2.ewm(span=period, adjust=False).mean()
    tema = (3 * ema1) - (3 * ema2) + ema3
    return tema.iloc[-1] if len(tema) > 0 else data['close'].iloc[-1]

values = [calculate_tema(df, parameters.get('period', 20))]
""",
        "parameters": {"period": 20},
        "is_free": True,
    },
    "Double Exponential Moving Average": {
        "name": "Double Exponential Moving Average",
        "description": "Double-smoothed EMA for trend following.",
        "category": "trend",
        "tags": "dema, double ema, moving average, trend",
        "code": """
# Double Exponential Moving Average (DEMA)
def calculate_dema(data, period=20):
    ema = data['close'].ewm(span=period, adjust=False).mean()
    ema_ema = ema.ewm(span=period, adjust=False).mean()
    dema = (2 * ema) - ema_ema
    return dema.iloc[-1] if len(dema) > 0 else data['close'].iloc[-1]

values = [calculate_dema(df, parameters.get('period', 20))]
""",
        "parameters": {"period": 20},
        "is_free": True,
    },
    "Variable Index Dynamic Average": {
        "name": "Variable Index Dynamic Average",
        "description": "Adaptive moving average that adjusts smoothing based on volatility.",
        "category": "trend",
        "tags": "vida, variable index, adaptive, moving average",
        "code": """
# Variable Index Dynamic Average (VIDA)
def calculate_vida(data, period=9):
    change = data['close'].diff().abs()
    volatility = change.rolling(period).sum()
    er = change / volatility
    sc = 2 / (period + 1)
    vida = data['close'].copy()
    for i in range(1, len(data)):
        alpha = sc * (1 + er.iloc[i])
        vida.iloc[i] = alpha * data['close'].iloc[i] + (1 - alpha) * vida.iloc[i-1]
    return vida.iloc[-1] if len(vida) > 0 else data['close'].iloc[-1]

values = [calculate_vida(df, parameters.get('period', 9))]
""",
        "parameters": {"period": 9},
        "is_free": True,
    },
    "Adaptive Moving Average": {
        "name": "Adaptive Moving Average",
        "description": "Moving average that adapts to market conditions using efficiency ratio.",
        "category": "trend",
        "tags": "ama, adaptive, moving average, efficiency ratio",
        "code": """
# Adaptive Moving Average (AMA)
def calculate_ama(data, period=10, fast=2, slow=30):
    change = abs(data['close'] - data['close'].shift(period))
    volatility = data['close'].diff().abs().rolling(period).sum()
    er = change / volatility
    sc = (er * (2/(fast+1) - 2/(slow+1)) + 2/(slow+1)) ** 2
    ama = data['close'].copy()
    for i in range(period, len(data)):
        ama.iloc[i] = ama.iloc[i-1] + sc.iloc[i] * (data['close'].iloc[i] - ama.iloc[i-1])
    return ama.iloc[-1] if len(ama) > 0 else data['close'].iloc[-1]

values = [calculate_ama(df,
    parameters.get('period', 10),
    parameters.get('fast', 2),
    parameters.get('slow', 30)
)]
""",
        "parameters": {"period": 10, "fast": 2, "slow": 30},
        "is_free": True,
    },
    "Fractal Adaptive Moving Average": {
        "name": "Fractal Adaptive Moving Average",
        "description": "Adaptive moving average based on fractal dimension of price series.",
        "category": "trend",
        "tags": "frama, fractal, adaptive, moving average",
        "code": """
# Fractal Adaptive Moving Average (FRAMA)
def calculate_frama(data, period=16):
    # Simplified FRAMA calculation
    high_max = data['high'].rolling(period).max()
    low_min = data['low'].rolling(period).min()
    n1 = (high_max - low_min) / period
    n2 = (high_max.shift(period) - low_min.shift(period)) / period
    n3 = (high_max - low_min) / (2 * period)
    d = (np.log(n1 + n2) - np.log(n3)) / np.log(2)
    alpha = np.exp(-4.6 * (d - 1))
    alpha = alpha.clip(0.01, 1.0)
    frama = data['close'].copy()
    for i in range(period, len(data)):
        frama.iloc[i] = alpha.iloc[i] * data['close'].iloc[i] + (1 - alpha.iloc[i]) * frama.iloc[i-1]
    return frama.iloc[-1] if len(frama) > 0 else data['close'].iloc[-1]

values = [calculate_frama(df, parameters.get('period', 16))]
""",
        "parameters": {"period": 16},
        "is_free": True,
    },
    "Moving Average Convergence": {
        "name": "Moving Average Convergence",
        "description": "Difference between two moving averages, showing trend direction.",
        "category": "trend",
        "tags": "mac, moving average convergence, trend",
        "code": """
# Moving Average Convergence (MAC)
def calculate_mac(data, fast=12, slow=26):
    sma_fast = data['close'].rolling(window=fast).mean()
    sma_slow = data['close'].rolling(window=slow).mean()
    mac = sma_fast - sma_slow
    return mac.iloc[-1] if len(mac) > 0 else 0.0

values = [calculate_mac(df,
    parameters.get('fast', 12),
    parameters.get('slow', 26)
)]
""",
        "parameters": {"fast": 12, "slow": 26},
        "is_free": True,
    },
    "Percentage B": {
        "name": "Percentage B",
        "description": "Bollinger Bands indicator showing position within bands as percentage.",
        "category": "volatility",
        "tags": "percentage b, bollinger, volatility",
        "code": """
# Percentage B (%B)
def calculate_percentage_b(data, period=20, std_dev=2):
    sma = data['close'].rolling(window=period).mean()
    std = data['close'].rolling(window=period).std()
    upper = sma + (std * std_dev)
    lower = sma - (std * std_dev)
    percent_b = ((data['close'] - lower) / (upper - lower)) * 100
    return percent_b.iloc[-1] if len(percent_b) > 0 else 50.0

values = [calculate_percentage_b(df,
    parameters.get('period', 20),
    parameters.get('std_dev', 2)
)]
""",
        "parameters": {"period": 20, "std_dev": 2},
        "is_free": True,
    },
    "Bandwidth": {
        "name": "Bandwidth",
        "description": "Bollinger Bands bandwidth indicator measuring volatility.",
        "category": "volatility",
        "tags": "bandwidth, bollinger, volatility",
        "code": """
# Bandwidth
def calculate_bandwidth(data, period=20, std_dev=2):
    sma = data['close'].rolling(window=period).mean()
    std = data['close'].rolling(window=period).std()
    upper = sma + (std * std_dev)
    lower = sma - (std * std_dev)
    bandwidth = ((upper - lower) / sma) * 100
    return bandwidth.iloc[-1] if len(bandwidth) > 0 else 0.0

values = [calculate_bandwidth(df,
    parameters.get('period', 20),
    parameters.get('std_dev', 2)
)]
""",
        "parameters": {"period": 20, "std_dev": 2},
        "is_free": True,
    },
    "Chande Momentum Oscillator": {
        "name": "Chande Momentum Oscillator",
        "description": "Momentum oscillator comparing sum of gains to sum of losses.",
        "category": "momentum",
        "tags": "cmo, chande, momentum, oscillator",
        "code": """
# Chande Momentum Oscillator (CMO)
def calculate_cmo(data, period=14):
    change = data['close'].diff()
    gains = change.where(change > 0, 0).rolling(period).sum()
    losses = -change.where(change < 0, 0).rolling(period).sum()
    cmo = ((gains - losses) / (gains + losses)) * 100
    return cmo.iloc[-1] if len(cmo) > 0 else 0.0

values = [calculate_cmo(df, parameters.get('period', 14))]
""",
        "parameters": {"period": 14},
        "is_free": True,
    },
    "Relative Momentum Index": {
        "name": "Relative Momentum Index",
        "description": "Momentum indicator similar to RSI but uses momentum instead of price change.",
        "category": "momentum",
        "tags": "rmi, relative momentum, momentum, oscillator",
        "code": """
# Relative Momentum Index (RMI)
def calculate_rmi(data, period=14, momentum_period=10):
    momentum = data['close'] - data['close'].shift(momentum_period)
    gains = momentum.where(momentum > 0, 0).rolling(period).mean()
    losses = -momentum.where(momentum < 0, 0).rolling(period).mean()
    rmi = 100 - (100 / (1 + gains / losses))
    return rmi.iloc[-1] if len(rmi) > 0 else 50.0

values = [calculate_rmi(df,
    parameters.get('period', 14),
    parameters.get('momentum_period', 10)
)]
""",
        "parameters": {"period": 14, "momentum_period": 10},
        "is_free": True,
    },
    "Stochastic RSI": {
        "name": "Stochastic RSI",
        "description": "Stochastic oscillator applied to RSI values for more sensitive signals.",
        "category": "momentum",
        "tags": "stoch rsi, stochastic, rsi, momentum",
        "code": """
# Stochastic RSI
def calculate_stoch_rsi(data, rsi_period=14, stoch_period=14):
    delta = data['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    rsi_min = rsi.rolling(stoch_period).min()
    rsi_max = rsi.rolling(stoch_period).max()
    stoch_rsi = ((rsi - rsi_min) / (rsi_max - rsi_min)) * 100
    return stoch_rsi.iloc[-1] if len(stoch_rsi) > 0 else 50.0

values = [calculate_stoch_rsi(df,
    parameters.get('rsi_period', 14),
    parameters.get('stoch_period', 14)
)]
""",
        "parameters": {"rsi_period": 14, "stoch_period": 14},
        "is_free": True,
    },
    "Fisher Transform": {
        "name": "Fisher Transform",
        "description": "Transforms prices into a Gaussian normal distribution for clearer signals.",
        "category": "momentum",
        "tags": "fisher transform, momentum, oscillator",
        "code": """
# Fisher Transform
def calculate_fisher_transform(data, period=10):
    high_low = data['high'] - data['low']
    value1 = (data['close'] - data['low']) / high_low
    value1 = value1.replace([np.inf, -np.inf], 0.5).fillna(0.5)
    value1 = value1.clip(0.001, 0.999)
    value2 = (2 * value1) - 1
    value2 = value2.clip(-0.999, 0.999)
    smoothed = value2.ewm(span=period, adjust=False).mean()
    fisher = 0.5 * np.log((1 + smoothed) / (1 - smoothed))
    return fisher.iloc[-1] if len(fisher) > 0 else 0.0

values = [calculate_fisher_transform(df, parameters.get('period', 10))]
""",
        "parameters": {"period": 10},
        "is_free": True,
    },
    "Ichimoku Conversion Line": {
        "name": "Ichimoku Conversion Line",
        "description": "Tenkan-sen line from Ichimoku system. Midpoint of 9-period high/low.",
        "category": "trend",
        "tags": "ichimoku, tenkan, conversion line, trend",
        "code": """
# Ichimoku Conversion Line (Tenkan-sen)
def calculate_tenkan_sen(data, period=9):
    high_max = data['high'].rolling(window=period).max()
    low_min = data['low'].rolling(window=period).min()
    tenkan = (high_max + low_min) / 2
    return tenkan.iloc[-1] if len(tenkan) > 0 else data['close'].iloc[-1]

values = [calculate_tenkan_sen(df, parameters.get('period', 9))]
""",
        "parameters": {"period": 9},
        "is_free": True,
    },
    "Ichimoku Base Line": {
        "name": "Ichimoku Base Line",
        "description": "Kijun-sen line from Ichimoku system. Midpoint of 26-period high/low.",
        "category": "trend",
        "tags": "ichimoku, kijun, base line, trend",
        "code": """
# Ichimoku Base Line (Kijun-sen)
def calculate_kijun_sen(data, period=26):
    high_max = data['high'].rolling(window=period).max()
    low_min = data['low'].rolling(window=period).min()
    kijun = (high_max + low_min) / 2
    return kijun.iloc[-1] if len(kijun) > 0 else data['close'].iloc[-1]

values = [calculate_kijun_sen(df, parameters.get('period', 26))]
""",
        "parameters": {"period": 26},
        "is_free": True,
    },
    "Ichimoku Leading Span A": {
        "name": "Ichimoku Leading Span A",
        "description": "Senkou Span A from Ichimoku. Average of Tenkan and Kijun, projected forward.",
        "category": "trend",
        "tags": "ichimoku, senkou span a, leading span, trend",
        "code": """
# Ichimoku Leading Span A (Senkou Span A)
def calculate_senkou_span_a(data, tenkan=9, kijun=26):
    tenkan_high = data['high'].rolling(window=tenkan).max()
    tenkan_low = data['low'].rolling(window=tenkan).min()
    tenkan_sen = (tenkan_high + tenkan_low) / 2
    kijun_high = data['high'].rolling(window=kijun).max()
    kijun_low = data['low'].rolling(window=kijun).min()
    kijun_sen = (kijun_high + kijun_low) / 2
    senkou_a = (tenkan_sen + kijun_sen) / 2
    return senkou_a.iloc[-1] if len(senkou_a) > 0 else data['close'].iloc[-1]

values = [calculate_senkou_span_a(df,
    parameters.get('tenkan', 9),
    parameters.get('kijun', 26)
)]
""",
        "parameters": {"tenkan": 9, "kijun": 26},
        "is_free": True,
    },
    "Ichimoku Leading Span B": {
        "name": "Ichimoku Leading Span B",
        "description": "Senkou Span B from Ichimoku. Midpoint of 52-period high/low, projected forward.",
        "category": "trend",
        "tags": "ichimoku, senkou span b, leading span, trend",
        "code": """
# Ichimoku Leading Span B (Senkou Span B)
def calculate_senkou_span_b(data, period=52):
    high_max = data['high'].rolling(window=period).max()
    low_min = data['low'].rolling(window=period).min()
    senkou_b = (high_max + low_min) / 2
    return senkou_b.iloc[-1] if len(senkou_b) > 0 else data['close'].iloc[-1]

values = [calculate_senkou_span_b(df, parameters.get('period', 52))]
""",
        "parameters": {"period": 52},
        "is_free": True,
    },
    "Ichimoku Lagging Span": {
        "name": "Ichimoku Lagging Span",
        "description": "Chikou Span from Ichimoku. Closing price projected backward.",
        "category": "trend",
        "tags": "ichimoku, chikou span, lagging span, trend",
        "code": """
# Ichimoku Lagging Span (Chikou Span)
def calculate_chikou_span(data, period=26):
    chikou = data['close'].shift(-period)
    return chikou.iloc[-1] if len(chikou) > 0 else data['close'].iloc[-1]

values = [calculate_chikou_span(df, parameters.get('period', 26))]
""",
        "parameters": {"period": 26},
        "is_free": True,
    },
    "Pivot Points": {
        "name": "Pivot Points",
        "description": "Support and resistance levels based on previous period's high, low, and close.",
        "category": "trend",
        "tags": "pivot points, support, resistance, levels",
        "code": """
# Pivot Points
def calculate_pivot_points(data):
    prev_high = data['high'].shift(1)
    prev_low = data['low'].shift(1)
    prev_close = data['close'].shift(1)
    pivot = (prev_high + prev_low + prev_close) / 3
    r1 = (2 * pivot) - prev_low
    s1 = (2 * pivot) - prev_high
    r2 = pivot + (prev_high - prev_low)
    s2 = pivot - (prev_high - prev_low)
    return {
        'pivot': pivot.iloc[-1] if len(pivot) > 0 else data['close'].iloc[-1],
        'r1': r1.iloc[-1] if len(r1) > 0 else data['close'].iloc[-1],
        'r2': r2.iloc[-1] if len(r2) > 0 else data['close'].iloc[-1],
        's1': s1.iloc[-1] if len(s1) > 0 else data['close'].iloc[-1],
        's2': s2.iloc[-1] if len(s2) > 0 else data['close'].iloc[-1]
    }

result = calculate_pivot_points(df)
output = result
values = [result['pivot']]
""",
        "parameters": {},
        "is_free": True,
    },
    "Fibonacci Retracement": {
        "name": "Fibonacci Retracement",
        "description": "Calculates Fibonacci retracement levels from swing high to swing low.",
        "category": "trend",
        "tags": "fibonacci, retracement, support, resistance",
        "code": """
# Fibonacci Retracement
def calculate_fibonacci_retracement(data, period=20):
    high = data['high'].rolling(window=period).max()
    low = data['low'].rolling(window=period).min()
    diff = high - low
    fib_levels = {
        '0.0': high.iloc[-1] if len(high) > 0 else data['close'].iloc[-1],
        '0.236': (high - diff * 0.236).iloc[-1] if len(high) > 0 else data['close'].iloc[-1],
        '0.382': (high - diff * 0.382).iloc[-1] if len(high) > 0 else data['close'].iloc[-1],
        '0.5': (high - diff * 0.5).iloc[-1] if len(high) > 0 else data['close'].iloc[-1],
        '0.618': (high - diff * 0.618).iloc[-1] if len(high) > 0 else data['close'].iloc[-1],
        '0.786': (high - diff * 0.786).iloc[-1] if len(high) > 0 else data['close'].iloc[-1],
        '1.0': low.iloc[-1] if len(low) > 0 else data['close'].iloc[-1]
    }
    return fib_levels

result = calculate_fibonacci_retracement(df, parameters.get('period', 20))
output = result
values = [result['0.5']]
""",
        "parameters": {"period": 20},
        "is_free": True,
    },
    "Price Channel": {
        "name": "Price Channel",
        "description": "Upper and lower bounds based on highest high and lowest low over period.",
        "category": "volatility",
        "tags": "price channel, volatility, support, resistance",
        "code": """
# Price Channel
def calculate_price_channel(data, period=20):
    upper = data['high'].rolling(window=period).max()
    lower = data['low'].rolling(window=period).min()
    return {
        'upper': upper.iloc[-1] if len(upper) > 0 else data['close'].iloc[-1],
        'lower': lower.iloc[-1] if len(lower) > 0 else data['close'].iloc[-1],
        'middle': (upper + lower).iloc[-1] / 2 if len(upper) > 0 else data['close'].iloc[-1]
    }

result = calculate_price_channel(df, parameters.get('period', 20))
output = result
values = [result['middle']]
""",
        "parameters": {"period": 20},
        "is_free": True,
    },
    "Linear Regression": {
        "name": "Linear Regression",
        "description": "Fits a linear regression line to price data to identify trend direction.",
        "category": "trend",
        "tags": "linear regression, trend, slope",
        "code": """
# Linear Regression
def calculate_linear_regression(data, period=20):
    x = np.arange(len(data))
    y = data['close'].values
    if len(y) >= period:
        x_window = x[-period:]
        y_window = y[-period:]
        slope = np.polyfit(x_window, y_window, 1)[0]
        intercept = np.polyfit(x_window, y_window, 1)[1]
        lr = slope * x[-1] + intercept
        return lr
    return data['close'].iloc[-1]

values = [calculate_linear_regression(df, parameters.get('period', 20))]
""",
        "parameters": {"period": 20},
        "is_free": True,
    },
    "Linear Regression Slope": {
        "name": "Linear Regression Slope",
        "description": "Slope of linear regression line indicating trend strength and direction.",
        "category": "trend",
        "tags": "linear regression slope, trend, strength",
        "code": """
# Linear Regression Slope
def calculate_lr_slope(data, period=20):
    x = np.arange(len(data))
    y = data['close'].values
    if len(y) >= period:
        x_window = x[-period:]
        y_window = y[-period:]
        slope = np.polyfit(x_window, y_window, 1)[0]
        return slope
    return 0.0

values = [calculate_lr_slope(df, parameters.get('period', 20))]
""",
        "parameters": {"period": 20},
        "is_free": True,
    },
    "Linear Regression R-Squared": {
        "name": "Linear Regression R-Squared",
        "description": "R-squared value of linear regression indicating how well price fits the trend line.",
        "category": "trend",
        "tags": "r-squared, linear regression, trend fit",
        "code": """
# Linear Regression R-Squared
def calculate_lr_rsquared(data, period=20):
    x = np.arange(len(data))
    y = data['close'].values
    if len(y) >= period:
        x_window = x[-period:]
        y_window = y[-period:]
        slope, intercept = np.polyfit(x_window, y_window, 1)
        y_pred = slope * x_window + intercept
        ss_res = np.sum((y_window - y_pred) ** 2)
        ss_tot = np.sum((y_window - np.mean(y_window)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        return r_squared
    return 0.0

values = [calculate_lr_rsquared(df, parameters.get('period', 20))]
""",
        "parameters": {"period": 20},
        "is_free": True,
    },
    "Time Series Forecast": {
        "name": "Time Series Forecast",
        "description": "Forecasts future price using linear regression projection.",
        "category": "trend",
        "tags": "forecast, linear regression, prediction",
        "code": """
# Time Series Forecast
def calculate_tsf(data, period=20, forecast_periods=1):
    x = np.arange(len(data))
    y = data['close'].values
    if len(y) >= period:
        x_window = x[-period:]
        y_window = y[-period:]
        slope, intercept = np.polyfit(x_window, y_window, 1)
        forecast = slope * (x[-1] + forecast_periods) + intercept
        return forecast
    return data['close'].iloc[-1]

values = [calculate_tsf(df,
    parameters.get('period', 20),
    parameters.get('forecast_periods', 1)
)]
""",
        "parameters": {"period": 20, "forecast_periods": 1},
        "is_free": True,
    },
    "Variance": {
        "name": "Variance",
        "description": "Measures price volatility as variance from mean.",
        "category": "volatility",
        "tags": "variance, volatility, statistical",
        "code": """
# Variance
def calculate_variance(data, period=20):
    variance = data['close'].rolling(window=period).var()
    return variance.iloc[-1] if len(variance) > 0 else 0.0

values = [calculate_variance(df, parameters.get('period', 20))]
""",
        "parameters": {"period": 20},
        "is_free": True,
    },
    "Coefficient of Variation": {
        "name": "Coefficient of Variation",
        "description": "Ratio of standard deviation to mean, showing relative volatility.",
        "category": "volatility",
        "tags": "coefficient of variation, volatility, relative",
        "code": """
# Coefficient of Variation
def calculate_coefficient_of_variation(data, period=20):
    mean = data['close'].rolling(window=period).mean()
    std = data['close'].rolling(window=period).std()
    cv = (std / mean) * 100
    return cv.iloc[-1] if len(cv) > 0 else 0.0

values = [calculate_coefficient_of_variation(df, parameters.get('period', 20))]
""",
        "parameters": {"period": 20},
        "is_free": True,
    },
    "Historical Volatility": {
        "name": "Historical Volatility",
        "description": "Annualized standard deviation of price returns.",
        "category": "volatility",
        "tags": "historical volatility, volatility, annualized",
        "code": """
# Historical Volatility
def calculate_historical_volatility(data, period=20, annualization=252):
    returns = data['close'].pct_change()
    std = returns.rolling(window=period).std()
    hv = std * np.sqrt(annualization) * 100
    return hv.iloc[-1] if len(hv) > 0 else 0.0

values = [calculate_historical_volatility(df,
    parameters.get('period', 20),
    parameters.get('annualization', 252)
)]
""",
        "parameters": {"period": 20, "annualization": 252},
        "is_free": True,
    },
    "Chaikin Oscillator": {
        "name": "Chaikin Oscillator",
        "description": "Difference between 3-day and 10-day EMAs of Accumulation/Distribution Line.",
        "category": "volume",
        "tags": "chaikin oscillator, volume, accumulation",
        "code": """
# Chaikin Oscillator
def calculate_chaikin_oscillator(data):
    clv = ((data['close'] - data['low']) - (data['high'] - data['close'])) / (data['high'] - data['low'])
    clv = clv.replace([np.inf, -np.inf], 0).fillna(0)
    ad = (clv * data['volume']).cumsum()
    ema_fast = ad.ewm(span=3, adjust=False).mean()
    ema_slow = ad.ewm(span=10, adjust=False).mean()
    co = ema_fast - ema_slow
    return co.iloc[-1] if len(co) > 0 else 0.0

values = [calculate_chaikin_oscillator(df)]
""",
        "parameters": {},
        "is_free": True,
    },
    "Ease of Movement": {
        "name": "Ease of Movement",
        "description": "Measures the relationship between price change and volume.",
        "category": "volume",
        "tags": "ease of movement, volume, price change",
        "code": """
# Ease of Movement (EOM)
def calculate_eom(data, period=14):
    distance = ((data['high'] + data['low']) / 2) - ((data['high'].shift() + data['low'].shift()) / 2)
    box_ratio = data['volume'] / (data['high'] - data['low'])
    eom = distance / box_ratio
    eom_sma = eom.rolling(window=period).mean()
    return eom_sma.iloc[-1] if len(eom_sma) > 0 else 0.0

values = [calculate_eom(df, parameters.get('period', 14))]
""",
        "parameters": {"period": 14},
        "is_free": True,
    },
    "Volume Weighted MACD": {
        "name": "Volume Weighted MACD",
        "description": "MACD calculated using volume-weighted prices.",
        "category": "volume",
        "tags": "vwmacd, volume weighted, macd",
        "code": """
# Volume Weighted MACD
def calculate_vwmacd(data, fast=12, slow=26, signal=9):
    vwap = (data['close'] * data['volume']).cumsum() / data['volume'].cumsum()
    ema_fast = vwap.ewm(span=fast, adjust=False).mean()
    ema_slow = vwap.ewm(span=slow, adjust=False).mean()
    macd = ema_fast - ema_slow
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    return {
        'macd': macd.iloc[-1] if len(macd) > 0 else 0.0,
        'signal': signal_line.iloc[-1] if len(signal_line) > 0 else 0.0
    }

result = calculate_vwmacd(df,
    parameters.get('fast', 12),
    parameters.get('slow', 26),
    parameters.get('signal', 9)
)
output = result
values = [result['macd']]
""",
        "parameters": {"fast": 12, "slow": 26, "signal": 9},
        "is_free": True,
    },
    "Volume Rate of Change": {
        "name": "Volume Rate of Change",
        "description": "Measures the rate of change in volume over a specified period.",
        "category": "volume",
        "tags": "volume roc, volume, rate of change",
        "code": """
# Volume Rate of Change
def calculate_volume_roc(data, period=12):
    vroc = ((data['volume'] - data['volume'].shift(period)) / data['volume'].shift(period)) * 100
    return vroc.iloc[-1] if len(vroc) > 0 else 0.0

values = [calculate_volume_roc(df, parameters.get('period', 12))]
""",
        "parameters": {"period": 12},
        "is_free": True,
    },
    "Price Volume Trend": {
        "name": "Price Volume Trend",
        "description": "Cumulative volume indicator that adds volume on price increases.",
        "category": "volume",
        "tags": "pvt, price volume trend, volume",
        "code": """
# Price Volume Trend (PVT)
def calculate_pvt(data):
    pvt = ((data['close'] - data['close'].shift()) / data['close'].shift()) * data['volume']
    pvt = pvt.fillna(0).cumsum()
    return pvt.iloc[-1] if len(pvt) > 0 else 0.0

values = [calculate_pvt(df)]
""",
        "parameters": {},
        "is_free": True,
    },
    "Volume Profile": {
        "name": "Volume Profile",
        "description": "Distribution of volume at different price levels.",
        "category": "volume",
        "tags": "volume profile, volume, distribution",
        "code": """
# Volume Profile (simplified)
def calculate_volume_profile(data, bins=24):
    min_price = data['low'].min()
    max_price = data['high'].max()
    price_range = max_price - min_price
    if price_range == 0:
        return data['close'].iloc[-1]
    bin_size = price_range / bins
    current_price = data['close'].iloc[-1]
    bin_index = int((current_price - min_price) / bin_size)
    return min_price + (bin_index * bin_size)

values = [calculate_volume_profile(df, parameters.get('bins', 24))]
""",
        "parameters": {"bins": 24},
        "is_free": True,
    },
    "Accumulation Swing Index": {
        "name": "Accumulation Swing Index",
        "description": "Cumulative indicator measuring price swings weighted by volatility.",
        "category": "momentum",
        "tags": "asi, accumulation swing index, momentum",
        "code": """
# Accumulation Swing Index (ASI)
def calculate_asi(data):
    k = 2
    r = data['high'] - data['close'].shift()
    r = r.where(r > abs(data['low'] - data['close'].shift()), abs(data['low'] - data['close'].shift()))
    r = r.where(r > abs(data['high'] - data['low']), abs(data['high'] - data['low']))
    si = 50 * ((data['close'] - data['close'].shift() + 0.5 * (data['close'] - data['open']) + 0.25 * (data['close'].shift() - data['open'].shift())) / r) * (k / max(data['high'] - data['low'], abs(data['close'] - data['close'].shift())))
    asi = si.fillna(0).cumsum()
    return asi.iloc[-1] if len(asi) > 0 else 0.0

values = [calculate_asi(df)]
""",
        "parameters": {},
        "is_free": True,
    },
    "Aroon Oscillator": {
        "name": "Aroon Oscillator",
        "description": "Difference between Aroon Up and Aroon Down.",
        "category": "trend",
        "tags": "aroon oscillator, trend, aroon",
        "code": """
# Aroon Oscillator
def calculate_aroon_oscillator(data, period=14):
    high_max = data['high'].rolling(window=period).max()
    low_min = data['low'].rolling(window=period).min()
    aroon_up = ((period - data['high'].rolling(period).apply(lambda x: period - 1 - x.argmax(), raw=True)) / period) * 100
    aroon_down = ((period - data['low'].rolling(period).apply(lambda x: period - 1 - x.argmin(), raw=True)) / period) * 100
    ao = aroon_up - aroon_down
    return ao.iloc[-1] if len(ao) > 0 else 0.0

values = [calculate_aroon_oscillator(df, parameters.get('period', 14))]
""",
        "parameters": {"period": 14},
        "is_free": True,
    },
    "Balance of Power": {
        "name": "Balance of Power",
        "description": "Measures the strength of buying vs selling pressure.",
        "category": "volume",
        "tags": "balance of power, volume, buying pressure, selling pressure",
        "code": """
# Balance of Power (BOP)
def calculate_bop(data):
    bop = (data['close'] - data['open']) / (data['high'] - data['low'])
    bop = bop.replace([np.inf, -np.inf], 0).fillna(0)
    return bop.iloc[-1] if len(bop) > 0 else 0.0

values = [calculate_bop(df)]
""",
        "parameters": {},
        "is_free": True,
    },
    "Commodity Channel Index": {
        "name": "Commodity Channel Index",
        "description": "Identifies cyclical trends. Values above +100 indicate overbought, below -100 oversold.",
        "category": "momentum",
        "tags": "cci, commodity, channel, momentum",
        "code": """
# Commodity Channel Index (CCI)
def calculate_cci(data, period=20):
    typical_price = (data['high'] + data['low'] + data['close']) / 3
    sma_tp = typical_price.rolling(window=period).mean()
    mean_dev = typical_price.rolling(window=period).apply(lambda x: np.mean(np.abs(x - x.mean())))
    cci = (typical_price - sma_tp) / (0.015 * mean_dev)
    return cci.iloc[-1] if len(cci) > 0 else 0.0

values = [calculate_cci(df, parameters.get('period', 20))]
""",
        "parameters": {"period": 20},
        "is_free": True,
    },
    "Money Flow Index": {
        "name": "Money Flow Index",
        "description": "Volume-weighted RSI. Values above 80 indicate overbought, below 20 oversold.",
        "category": "volume",
        "tags": "mfi, money flow, volume, rsi",
        "code": """
# Money Flow Index (MFI)
def calculate_mfi(data, period=14):
    typical_price = (data['high'] + data['low'] + data['close']) / 3
    raw_money_flow = typical_price * data['volume']
    positive_flow = raw_money_flow.where(typical_price > typical_price.shift(), 0).rolling(window=period).sum()
    negative_flow = raw_money_flow.where(typical_price < typical_price.shift(), 0).rolling(window=period).sum()
    mfi = 100 - (100 / (1 + positive_flow / negative_flow))
    return mfi.iloc[-1] if len(mfi) > 0 else 50.0

values = [calculate_mfi(df, parameters.get('period', 14))]
""",
        "parameters": {"period": 14},
        "is_free": True,
    },
    # Additional advanced indicators (expanding to 100+)
    "Schaff Trend Cycle": {
        "name": "Schaff Trend Cycle",
        "description": "Combines MACD and Stochastic to identify trend cycles.",
        "category": "momentum",
        "tags": "stc, schaff trend cycle, macd, stochastic",
        "code": """
# Schaff Trend Cycle (STC)
def calculate_stc(data, fast=23, slow=50, cycle=10):
    macd = data['close'].ewm(span=fast, adjust=False).mean() - data['close'].ewm(span=slow, adjust=False).mean()
    macd_min = macd.rolling(window=cycle).min()
    macd_max = macd.rolling(window=cycle).max()
    stoch_macd = 100 * (macd - macd_min) / (macd_max - macd_min)
    stoch_macd = stoch_macd.fillna(50)
    stc = stoch_macd.ewm(span=cycle, adjust=False).mean()
    return stc.iloc[-1] if len(stc) > 0 else 50.0

values = [calculate_stc(df,
    parameters.get('fast', 23),
    parameters.get('slow', 50),
    parameters.get('cycle', 10)
)]
""",
        "parameters": {"fast": 23, "slow": 50, "cycle": 10},
        "is_free": True,
    },
    "TRIX": {
        "name": "TRIX",
        "description": "Triple-smoothed rate of change indicator showing momentum.",
        "category": "momentum",
        "tags": "trix, momentum, rate of change",
        "code": """
# TRIX
def calculate_trix(data, period=14):
    ema1 = data['close'].ewm(span=period, adjust=False).mean()
    ema2 = ema1.ewm(span=period, adjust=False).mean()
    ema3 = ema2.ewm(span=period, adjust=False).mean()
    trix = ((ema3 - ema3.shift(1)) / ema3.shift(1)) * 100
    return trix.iloc[-1] if len(trix) > 0 else 0.0

values = [calculate_trix(df, parameters.get('period', 14))]
""",
        "parameters": {"period": 14},
        "is_free": True,
    },
    "Mass Index": {
        "name": "Mass Index",
        "description": "Measures trend reversals by analyzing price range expansion.",
        "category": "volatility",
        "tags": "mass index, volatility, trend reversal",
        "code": """
# Mass Index
def calculate_mass_index(data, period=25, sum_period=9):
    high_low = data['high'] - data['low']
    ema = high_low.ewm(span=period, adjust=False).mean()
    ema_ema = ema.ewm(span=period, adjust=False).mean()
    ratio = ema / ema_ema
    mass_index = ratio.rolling(window=sum_period).sum()
    return mass_index.iloc[-1] if len(mass_index) > 0 else 0.0

values = [calculate_mass_index(df,
    parameters.get('period', 25),
    parameters.get('sum_period', 9)
)]
""",
        "parameters": {"period": 25, "sum_period": 9},
        "is_free": True,
    },
    "On Balance Volume": {
        "name": "On Balance Volume",
        "description": "Cumulative volume indicator that adds volume on up days and subtracts on down days.",
        "category": "volume",
        "tags": "obv, on balance volume, volume, trend",
        "code": """
# On Balance Volume (OBV)
def calculate_obv(data):
    obv = (data['volume'] * np.sign(data['close'].diff())).fillna(0).cumsum()
    return obv.iloc[-1] if len(obv) > 0 else 0.0

values = [calculate_obv(df)]
""",
        "parameters": {},
        "is_free": True,
    },
    "Williams %R": {
        "name": "Williams %R",
        "description": "Momentum oscillator measuring overbought/oversold conditions. Values above -20 overbought, below -80 oversold.",
        "category": "momentum",
        "tags": "williams r, williams percent r, momentum, oscillator",
        "code": """
# Williams %R
def calculate_williams_r(data, period=14):
    highest_high = data['high'].rolling(window=period).max()
    lowest_low = data['low'].rolling(window=period).min()
    wr = -100 * (highest_high - data['close']) / (highest_high - lowest_low)
    return wr.iloc[-1] if len(wr) > 0 else -50.0

values = [calculate_williams_r(df, parameters.get('period', 14))]
""",
        "parameters": {"period": 14},
        "is_free": True,
    },
    "Average True Range": {
        "name": "Average True Range",
        "description": "Measures market volatility using true range.",
        "category": "volatility",
        "tags": "atr, average true range, volatility",
        "code": """
# Average True Range (ATR)
def calculate_atr(data, period=14):
    high_low = data['high'] - data['low']
    high_close = np.abs(data['high'] - data['close'].shift())
    low_close = np.abs(data['low'] - data['close'].shift())
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = true_range.rolling(window=period).mean()
    return atr.iloc[-1] if len(atr) > 0 else 0.0

values = [calculate_atr(df, parameters.get('period', 14))]
""",
        "parameters": {"period": 14},
        "is_free": True,
    },
    "Parabolic SAR": {
        "name": "Parabolic SAR",
        "description": "Trend-following indicator that provides entry and exit points.",
        "category": "trend",
        "tags": "parabolic sar, sar, trend, stop loss",
        "code": """
# Parabolic SAR
def calculate_parabolic_sar(data, af_start=0.02, af_increment=0.02, af_max=0.2):
    high = data['high'].values
    low = data['low'].values
    close = data['close'].values
    sar = np.zeros(len(data))
    ep = np.zeros(len(data))
    af = np.zeros(len(data))
    trend = np.zeros(len(data))
    
    sar[0] = low[0]
    ep[0] = high[0]
    af[0] = af_start
    trend[0] = 1
    
    for i in range(1, len(data)):
        if trend[i-1] == 1:
            sar[i] = sar[i-1] + af[i-1] * (ep[i-1] - sar[i-1])
            if sar[i] > low[i-1]:
                sar[i] = low[i-1]
            if high[i] > ep[i-1]:
                ep[i] = high[i]
                af[i] = min(af[i-1] + af_increment, af_max)
            else:
                ep[i] = ep[i-1]
                af[i] = af[i-1]
            if low[i] < sar[i]:
                trend[i] = -1
                sar[i] = ep[i-1]
                ep[i] = low[i]
                af[i] = af_start
            else:
                trend[i] = 1
        else:
            sar[i] = sar[i-1] + af[i-1] * (ep[i-1] - sar[i-1])
            if sar[i] < high[i-1]:
                sar[i] = high[i-1]
            if low[i] < ep[i-1]:
                ep[i] = low[i]
                af[i] = min(af[i-1] + af_increment, af_max)
            else:
                ep[i] = ep[i-1]
                af[i] = af[i-1]
            if high[i] > sar[i]:
                trend[i] = 1
                sar[i] = ep[i-1]
                ep[i] = high[i]
                af[i] = af_start
            else:
                trend[i] = -1
    
    return sar[-1] if len(sar) > 0 else data['close'].iloc[-1]

values = [calculate_parabolic_sar(df,
    parameters.get('af_start', 0.02),
    parameters.get('af_increment', 0.02),
    parameters.get('af_max', 0.2)
)]
""",
        "parameters": {"af_start": 0.02, "af_increment": 0.02, "af_max": 0.2},
        "is_free": True,
    },
    "Average Directional Index": {
        "name": "Average Directional Index",
        "description": "Measures trend strength without regard to direction. Values above 25 indicate strong trend.",
        "category": "trend",
        "tags": "adx, average directional index, trend strength",
        "code": """
# Average Directional Index (ADX)
def calculate_adx(data, period=14):
    high_diff = data['high'].diff()
    low_diff = -data['low'].diff()
    plus_dm = high_diff.where((high_diff > low_diff) & (high_diff > 0), 0)
    minus_dm = low_diff.where((low_diff > high_diff) & (low_diff > 0), 0)
    tr = pd.concat([data['high'] - data['low'],
                    abs(data['high'] - data['close'].shift()),
                    abs(data['low'] - data['close'].shift())], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    plus_di = 100 * (plus_dm.rolling(period).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(period).mean() / atr)
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    adx = dx.rolling(window=period).mean()
    return adx.iloc[-1] if len(adx) > 0 else 0.0

values = [calculate_adx(df, parameters.get('period', 14))]
""",
        "parameters": {"period": 14},
        "is_free": True,
    },
    "Stochastic Oscillator": {
        "name": "Stochastic Oscillator",
        "description": "Momentum indicator comparing closing price to price range. Values above 80 overbought, below 20 oversold.",
        "category": "momentum",
        "tags": "stochastic, momentum, oscillator, overbought, oversold",
        "code": """
# Stochastic Oscillator
def calculate_stochastic(data, k_period=14, d_period=3):
    lowest_low = data['low'].rolling(window=k_period).min()
    highest_high = data['high'].rolling(window=k_period).max()
    k = 100 * (data['close'] - lowest_low) / (highest_high - lowest_low)
    d = k.rolling(window=d_period).mean()
    return {
        'k': k.iloc[-1] if len(k) > 0 else 50.0,
        'd': d.iloc[-1] if len(d) > 0 else 50.0
    }

result = calculate_stochastic(df,
    parameters.get('k_period', 14),
    parameters.get('d_period', 3)
)
output = result
values = [result['k']]
""",
        "parameters": {"k_period": 14, "d_period": 3},
        "is_free": True,
    },
    "Relative Strength Index": {
        "name": "Relative Strength Index",
        "description": "Momentum oscillator measuring speed and magnitude of price changes. Values above 70 overbought, below 30 oversold.",
        "category": "momentum",
        "tags": "rsi, relative strength index, momentum, oscillator",
        "code": """
# Relative Strength Index (RSI)
def calculate_rsi(data, period=14):
    delta = data['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1] if len(rsi) > 0 else 50.0

values = [calculate_rsi(df, parameters.get('period', 14))]
""",
        "parameters": {"period": 14},
        "is_free": True,
    },
    "Moving Average Convergence Divergence": {
        "name": "Moving Average Convergence Divergence",
        "description": "Trend-following momentum indicator showing relationship between two EMAs.",
        "category": "trend",
        "tags": "macd, moving average convergence divergence, trend, momentum",
        "code": """
# Moving Average Convergence Divergence (MACD)
def calculate_macd(data, fast=12, slow=26, signal=9):
    ema_fast = data['close'].ewm(span=fast, adjust=False).mean()
    ema_slow = data['close'].ewm(span=slow, adjust=False).mean()
    macd = ema_fast - ema_slow
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    histogram = macd - signal_line
    return {
        'macd': macd.iloc[-1] if len(macd) > 0 else 0.0,
        'signal': signal_line.iloc[-1] if len(signal_line) > 0 else 0.0,
        'histogram': histogram.iloc[-1] if len(histogram) > 0 else 0.0
    }

result = calculate_macd(df,
    parameters.get('fast', 12),
    parameters.get('slow', 26),
    parameters.get('signal', 9)
)
output = result
values = [result['macd']]
""",
        "parameters": {"fast": 12, "slow": 26, "signal": 9},
        "is_free": True,
    },
    "Bollinger Bands": {
        "name": "Bollinger Bands",
        "description": "Volatility bands placed above and below a moving average.",
        "category": "volatility",
        "tags": "bollinger bands, volatility, bands, support, resistance",
        "code": """
# Bollinger Bands
def calculate_bollinger_bands(data, period=20, std_dev=2):
    sma = data['close'].rolling(window=period).mean()
    std = data['close'].rolling(window=period).std()
    upper = sma + (std * std_dev)
    lower = sma - (std * std_dev)
    return {
        'upper': upper.iloc[-1] if len(upper) > 0 else data['close'].iloc[-1],
        'middle': sma.iloc[-1] if len(sma) > 0 else data['close'].iloc[-1],
        'lower': lower.iloc[-1] if len(lower) > 0 else data['close'].iloc[-1]
    }

result = calculate_bollinger_bands(df,
    parameters.get('period', 20),
    parameters.get('std_dev', 2)
)
output = result
values = [result['middle']]
""",
        "parameters": {"period": 20, "std_dev": 2},
        "is_free": True,
    },
    "Simple Moving Average": {
        "name": "Simple Moving Average",
        "description": "Average of closing prices over a specified period.",
        "category": "trend",
        "tags": "sma, simple moving average, trend, average",
        "code": """
# Simple Moving Average (SMA)
def calculate_sma(data, period=20):
    sma = data['close'].rolling(window=period).mean()
    return sma.iloc[-1] if len(sma) > 0 else data['close'].iloc[-1]

values = [calculate_sma(df, parameters.get('period', 20))]
""",
        "parameters": {"period": 20},
        "is_free": True,
    },
    "Exponential Moving Average": {
        "name": "Exponential Moving Average",
        "description": "Weighted moving average that gives more weight to recent prices.",
        "category": "trend",
        "tags": "ema, exponential moving average, trend, weighted",
        "code": """
# Exponential Moving Average (EMA)
def calculate_ema(data, period=20):
    ema = data['close'].ewm(span=period, adjust=False).mean()
    return ema.iloc[-1] if len(ema) > 0 else data['close'].iloc[-1]

values = [calculate_ema(df, parameters.get('period', 20))]
""",
        "parameters": {"period": 20},
        "is_free": True,
    },
    "Weighted Moving Average": {
        "name": "Weighted Moving Average",
        "description": "Moving average that gives more weight to recent data points.",
        "category": "trend",
        "tags": "wma, weighted moving average, trend",
        "code": """
# Weighted Moving Average (WMA)
def calculate_wma(data, period=20):
    weights = np.arange(1, period + 1)
    wma = data['close'].rolling(window=period).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)
    return wma.iloc[-1] if len(wma) > 0 else data['close'].iloc[-1]

values = [calculate_wma(df, parameters.get('period', 20))]
""",
        "parameters": {"period": 20},
        "is_free": True,
    },
    "Volume Weighted Average Price": {
        "name": "Volume Weighted Average Price",
        "description": "Average price weighted by volume over a specified period.",
        "category": "volume",
        "tags": "vwap, volume weighted average price, volume, price",
        "code": """
# Volume Weighted Average Price (VWAP)
def calculate_vwap(data, period=None):
    if period:
        typical_price = (data['high'] + data['low'] + data['close']) / 3
        vwap = (typical_price * data['volume']).rolling(window=period).sum() / data['volume'].rolling(window=period).sum()
    else:
        typical_price = (data['high'] + data['low'] + data['close']) / 3
        vwap = (typical_price * data['volume']).cumsum() / data['volume'].cumsum()
    return vwap.iloc[-1] if len(vwap) > 0 else data['close'].iloc[-1]

values = [calculate_vwap(df, parameters.get('period', None))]
""",
        "parameters": {"period": None},
        "is_free": True,
    },
    "Rate of Change": {
        "name": "Rate of Change",
        "description": "Measures the percentage change in price over a specified period.",
        "category": "momentum",
        "tags": "roc, rate of change, momentum",
        "code": """
# Rate of Change (ROC)
def calculate_roc(data, period=12):
    roc = ((data['close'] - data['close'].shift(period)) / data['close'].shift(period)) * 100
    return roc.iloc[-1] if len(roc) > 0 else 0.0

values = [calculate_roc(df, parameters.get('period', 12))]
""",
        "parameters": {"period": 12},
        "is_free": True,
    },
    "Momentum": {
        "name": "Momentum",
        "description": "Measures the rate of change in price over a specified period.",
        "category": "momentum",
        "tags": "momentum, rate of change",
        "code": """
# Momentum
def calculate_momentum(data, period=10):
    momentum = data['close'] - data['close'].shift(period)
    return momentum.iloc[-1] if len(momentum) > 0 else 0.0

values = [calculate_momentum(df, parameters.get('period', 10))]
""",
        "parameters": {"period": 10},
        "is_free": True,
    },
    "Aroon": {
        "name": "Aroon",
        "description": "Identifies trend changes and strength. Aroon Up measures time since highest high, Aroon Down measures time since lowest low.",
        "category": "trend",
        "tags": "aroon, trend, strength",
        "code": """
# Aroon
def calculate_aroon(data, period=14):
    high_max = data['high'].rolling(window=period).max()
    low_min = data['low'].rolling(window=period).min()
    aroon_up = ((period - data['high'].rolling(period).apply(lambda x: period - 1 - x.argmax(), raw=True)) / period) * 100
    aroon_down = ((period - data['low'].rolling(period).apply(lambda x: period - 1 - x.argmin(), raw=True)) / period) * 100
    return {
        'aroon_up': aroon_up.iloc[-1] if len(aroon_up) > 0 else 50.0,
        'aroon_down': aroon_down.iloc[-1] if len(aroon_down) > 0 else 50.0
    }

result = calculate_aroon(df, parameters.get('period', 14))
output = result
values = [result['aroon_up']]
""",
        "parameters": {"period": 14},
        "is_free": True,
    },
    "Chaikin Money Flow": {
        "name": "Chaikin Money Flow",
        "description": "Volume-weighted accumulation/distribution indicator. Values above 0 indicate buying pressure, below 0 selling pressure.",
        "category": "volume",
        "tags": "cmf, chaikin money flow, volume, accumulation",
        "code": """
# Chaikin Money Flow (CMF)
def calculate_cmf(data, period=20):
    clv = ((data['close'] - data['low']) - (data['high'] - data['close'])) / (data['high'] - data['low'])
    clv = clv.replace([np.inf, -np.inf], 0).fillna(0)
    cmf = (clv * data['volume']).rolling(window=period).sum() / data['volume'].rolling(window=period).sum()
    return cmf.iloc[-1] if len(cmf) > 0 else 0.0

values = [calculate_cmf(df, parameters.get('period', 20))]
""",
        "parameters": {"period": 20},
        "is_free": True,
    },
    "Donchian Channels": {
        "name": "Donchian Channels",
        "description": "Volatility bands based on highest high and lowest low over a period.",
        "category": "volatility",
        "tags": "donchian channels, volatility, bands",
        "code": """
# Donchian Channels
def calculate_donchian(data, period=20):
    upper = data['high'].rolling(window=period).max()
    lower = data['low'].rolling(window=period).min()
    middle = (upper + lower) / 2
    return {
        'upper': upper.iloc[-1] if len(upper) > 0 else data['close'].iloc[-1],
        'middle': middle.iloc[-1] if len(middle) > 0 else data['close'].iloc[-1],
        'lower': lower.iloc[-1] if len(lower) > 0 else data['close'].iloc[-1]
    }

result = calculate_donchian(df, parameters.get('period', 20))
output = result
values = [result['middle']]
""",
        "parameters": {"period": 20},
        "is_free": True,
    },
    "Keltner Channels": {
        "name": "Keltner Channels",
        "description": "Volatility bands based on ATR around an EMA.",
        "category": "volatility",
        "tags": "keltner channels, volatility, bands, atr",
        "code": """
# Keltner Channels
def calculate_keltner(data, period=20, multiplier=2.0):
    ema = data['close'].ewm(span=period, adjust=False).mean()
    high_low = data['high'] - data['low']
    high_close = np.abs(data['high'] - data['close'].shift())
    low_close = np.abs(data['low'] - data['close'].shift())
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = true_range.rolling(window=period).mean()
    upper = ema + (atr * multiplier)
    lower = ema - (atr * multiplier)
    return {
        'upper': upper.iloc[-1] if len(upper) > 0 else data['close'].iloc[-1],
        'middle': ema.iloc[-1] if len(ema) > 0 else data['close'].iloc[-1],
        'lower': lower.iloc[-1] if len(lower) > 0 else data['close'].iloc[-1]
    }

result = calculate_keltner(df,
    parameters.get('period', 20),
    parameters.get('multiplier', 2.0)
)
output = result
values = [result['middle']]
""",
        "parameters": {"period": 20, "multiplier": 2.0},
        "is_free": True,
    },
    "Standard Deviation": {
        "name": "Standard Deviation",
        "description": "Measures price volatility as standard deviation from moving average.",
        "category": "volatility",
        "tags": "standard deviation, volatility, std",
        "code": """
# Standard Deviation
def calculate_std(data, period=20):
    sma = data['close'].rolling(window=period).mean()
    std = data['close'].rolling(window=period).std()
    return {
        'std': std.iloc[-1] if len(std) > 0 else 0.0,
        'mean': sma.iloc[-1] if len(sma) > 0 else data['close'].iloc[-1]
    }

result = calculate_std(df, parameters.get('period', 20))
output = result
values = [result['std']]
""",
        "parameters": {"period": 20},
        "is_free": True,
    },
    "Price Channels": {
        "name": "Price Channels",
        "description": "Upper and lower bounds based on highest high and lowest low.",
        "category": "volatility",
        "tags": "price channels, volatility, support, resistance",
        "code": """
# Price Channels
def calculate_price_channels(data, period=20):
    upper = data['high'].rolling(window=period).max()
    lower = data['low'].rolling(window=period).min()
    return {
        'upper': upper.iloc[-1] if len(upper) > 0 else data['close'].iloc[-1],
        'lower': lower.iloc[-1] if len(lower) > 0 else data['close'].iloc[-1]
    }

result = calculate_price_channels(df, parameters.get('period', 20))
output = result
values = [(result['upper'] + result['lower']) / 2]
""",
        "parameters": {"period": 20},
        "is_free": True,
    },
    "Z-Score": {
        "name": "Z-Score",
        "description": "Measures how many standard deviations a price is from the mean.",
        "category": "volatility",
        "tags": "z-score, standard deviation, mean reversion",
        "code": """
# Z-Score
def calculate_zscore(data, period=20):
    sma = data['close'].rolling(window=period).mean()
    std = data['close'].rolling(window=period).std()
    zscore = (data['close'] - sma) / std
    return zscore.iloc[-1] if len(zscore) > 0 else 0.0

values = [calculate_zscore(df, parameters.get('period', 20))]
""",
        "parameters": {"period": 20},
        "is_free": True,
    },
    "Elder Ray Index": {
        "name": "Elder Ray Index",
        "description": "Measures buying and selling pressure using EMA and price extremes.",
        "category": "momentum",
        "tags": "elder ray, buying pressure, selling pressure, ema",
        "code": """
# Elder Ray Index
def calculate_elder_ray(data, period=13):
    ema = data['close'].ewm(span=period, adjust=False).mean()
    bull_power = data['high'] - ema
    bear_power = data['low'] - ema
    return {
        'bull_power': bull_power.iloc[-1] if len(bull_power) > 0 else 0.0,
        'bear_power': bear_power.iloc[-1] if len(bear_power) > 0 else 0.0
    }

result = calculate_elder_ray(df, parameters.get('period', 13))
output = result
values = [result['bull_power']]
""",
        "parameters": {"period": 13},
        "is_free": True,
    },
    "Force Index": {
        "name": "Force Index",
        "description": "Combines price and volume to measure buying and selling pressure.",
        "category": "volume",
        "tags": "force index, volume, price, pressure",
        "code": """
# Force Index
def calculate_force_index(data, period=13):
    fi = data['close'].diff() * data['volume']
    fi_ema = fi.ewm(span=period, adjust=False).mean()
    return fi_ema.iloc[-1] if len(fi_ema) > 0 else 0.0

values = [calculate_force_index(df, parameters.get('period', 13))]
""",
        "parameters": {"period": 13},
        "is_free": True,
    },
    "Ease of Movement": {
        "name": "Ease of Movement",
        "description": "Measures the relationship between price change and volume.",
        "category": "volume",
        "tags": "ease of movement, volume, price change",
        "code": """
# Ease of Movement (EOM)
def calculate_eom(data, period=14):
    distance = ((data['high'] + data['low']) / 2) - ((data['high'].shift() + data['low'].shift()) / 2)
    box_ratio = data['volume'] / (data['high'] - data['low'])
    eom = distance / box_ratio
    eom_sma = eom.rolling(window=period).mean()
    return eom_sma.iloc[-1] if len(eom_sma) > 0 else 0.0

values = [calculate_eom(df, parameters.get('period', 14))]
""",
        "parameters": {"period": 14},
        "is_free": True,
    },
    "Vortex Indicator": {
        "name": "Vortex Indicator",
        "description": "Identifies trend direction using positive and negative trend movement.",
        "category": "trend",
        "tags": "vortex, trend, direction",
        "code": """
# Vortex Indicator
def calculate_vortex(data, period=14):
    tr = pd.concat([data['high'] - data['low'],
                    abs(data['high'] - data['close'].shift()),
                    abs(data['low'] - data['close'].shift())], axis=1).max(axis=1)
    vm_plus = abs(data['high'] - data['low'].shift())
    vm_minus = abs(data['low'] - data['high'].shift())
    vi_plus = vm_plus.rolling(window=period).sum() / tr.rolling(window=period).sum()
    vi_minus = vm_minus.rolling(window=period).sum() / tr.rolling(window=period).sum()
    return {
        'vi_plus': vi_plus.iloc[-1] if len(vi_plus) > 0 else 0.0,
        'vi_minus': vi_minus.iloc[-1] if len(vi_minus) > 0 else 0.0
    }

result = calculate_vortex(df, parameters.get('period', 14))
output = result
values = [result['vi_plus']]
""",
        "parameters": {"period": 14},
        "is_free": True,
    },
    "Negative Volume Index": {
        "name": "Negative Volume Index",
        "description": "Tracks price changes on days with decreased volume.",
        "category": "volume",
        "tags": "nvi, negative volume, volume, price",
        "code": """
# Negative Volume Index (NVI)
def calculate_nvi(data):
    price_change = data['close'].pct_change()
    nvi = 1000  # Starting value
    for i in range(1, len(data)):
        if data['volume'].iloc[i] < data['volume'].iloc[i-1]:
            nvi = nvi * (1 + price_change.iloc[i])
    return nvi

values = [calculate_nvi(df)]
""",
        "parameters": {},
        "is_free": True,
    },
    "Positive Volume Index": {
        "name": "Positive Volume Index",
        "description": "Tracks price changes on days with increased volume.",
        "category": "volume",
        "tags": "pvi, positive volume, volume, price",
        "code": """
# Positive Volume Index (PVI)
def calculate_pvi(data):
    price_change = data['close'].pct_change()
    pvi = 1000  # Starting value
    for i in range(1, len(data)):
        if data['volume'].iloc[i] > data['volume'].iloc[i-1]:
            pvi = pvi * (1 + price_change.iloc[i])
    return pvi

values = [calculate_pvi(df)]
""",
        "parameters": {},
        "is_free": True,
    },
}


async def populate_library(admin_user_id: int = 1):
    """
    Populate the indicator library with common indicators.

    Args:
        admin_user_id: User ID to assign as developer (default: 1)
    """
    async with async_session() as session:
        try:
            # Verify admin user exists
            admin_user = await session.get(User, admin_user_id)
            if not admin_user:
                logger.error(f"Admin user {admin_user_id} not found")
                return

            created_count = 0
            skipped_count = 0

            for indicator_key, indicator_data in INDICATOR_LIBRARY.items():
                # Check if indicator already exists
                existing_result = await session.execute(
                    select(Indicator).where(Indicator.name == indicator_data["name"])
                )
                existing = existing_result.scalar_one_or_none()

                if existing:
                    logger.debug(
                        f"Indicator '{indicator_data['name']}' already exists, skipping"
                    )
                    skipped_count += 1
                    continue

                # Create indicator
                indicator = Indicator(
                    developer_id=admin_user_id,
                    name=indicator_data["name"],
                    description=indicator_data["description"],
                    category=indicator_data["category"],
                    tags=indicator_data["tags"],
                    code=indicator_data["code"],
                    language=IndicatorLanguage.PYTHON.value,
                    parameters=indicator_data["parameters"],
                    price=0.0,
                    is_free=indicator_data["is_free"],
                    status=IndicatorStatus.APPROVED.value,  # Pre-approved library indicators
                    is_public=True,
                )

                session.add(indicator)
                await session.flush()  # Get indicator.id

                # Create initial version
                version = IndicatorVersion(
                    indicator_id=indicator.id,
                    version=1,
                    version_name="1.0.0",
                    code=indicator_data["code"],
                    parameters=indicator_data["parameters"],
                    is_active=True,
                )

                session.add(version)
                indicator.latest_version_id = version.id

                created_count += 1
                logger.info(f"Created indicator: {indicator_data['name']}")

            await session.commit()
            logger.info(
                f"Indicator library population complete: {created_count} created, {skipped_count} skipped"
            )

            return {
                "created": created_count,
                "skipped": skipped_count,
                "total": len(INDICATOR_LIBRARY),
            }
        except Exception as e:
            logger.error(f"Error populating indicator library: {e}", exc_info=True)
            await session.rollback()
            raise


if __name__ == "__main__":
    # Run population script
    asyncio.run(populate_library())
