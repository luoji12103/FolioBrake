import numpy as np
import pandas as pd

def obv(close: list[float], volume: list[float]) -> list[float]:
    obv = np.zeros(len(close))
    for i in range(1, len(close)):
        if close[i] > close[i-1]:
            obv[i] = obv[i-1] + volume[i]
        elif close[i] < close[i-1]:
            obv[i] = obv[i-1] - volume[i]
        else:
            obv[i] = obv[i-1]
    return obv.tolist()

def vwap(high: list[float], low: list[float], close: list[float], volume: list[float]) -> list[float]:
    typical_price = (np.array(high) + np.array(low) + np.array(close)) / 3
    cumulative_tp_volume = np.cumsum(typical_price * np.array(volume))
    cumulative_volume = np.cumsum(volume)
    return (cumulative_tp_volume / cumulative_volume).tolist()
