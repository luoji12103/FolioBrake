import numpy as np
import pandas as pd

def bollinger_bands(prices: list[float], window: int = 20, num_std: float = 2.0) -> dict:
    s = pd.Series(prices)
    middle = s.rolling(window=window).mean()
    std = s.rolling(window=window).std()
    upper = middle + num_std * std
    lower = middle - num_std * std
    return {
        "upper": upper.tolist(),
        "middle": middle.tolist(),
        "lower": lower.tolist()
    }

def atr(high: list[float], low: list[float], close: list[float], period: int = 14) -> list[float]:
    tr = np.maximum(np.array(high) - np.array(low),
                    np.maximum(np.abs(np.array(high) - np.roll(np.array(close), 1)),
                              np.abs(np.array(low) - np.roll(np.array(close), 1))))
    return pd.Series(tr).rolling(window=period).mean().tolist()
