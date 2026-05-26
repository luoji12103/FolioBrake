import numpy as np
import pandas as pd

def sma(prices: list[float], window: int) -> list[float]:
    return pd.Series(prices).rolling(window=window).mean().tolist()

def ema(prices: list[float], window: int) -> list[float]:
    return pd.Series(prices).ewm(span=window, adjust=False).mean().tolist()

def wma(prices: list[float], window: int) -> list[float]:
    weights = np.arange(1, window + 1)
    return pd.Series(prices).rolling(window=window).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True).tolist()
