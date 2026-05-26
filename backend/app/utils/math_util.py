import numpy as np

def percent_change(old: float, new: float) -> float:
    if old == 0:
        return 0.0
    return ((new - old) / old) * 100

def moving_average(data: list[float], window: int) -> list[float]:
    return np.convolve(data, np.ones(window)/window, mode='valid').tolist()

def standard_deviation(data: list[float]) -> float:
    return float(np.std(data))
