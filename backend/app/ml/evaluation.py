import numpy as np

def accuracy(y_true: list, y_pred: list) -> float:
    correct = sum(1 for t, p in zip(y_true, y_pred) if t == p)
    return correct / len(y_true) if y_true else 0.0

def mse(y_true: list[float], y_pred: list[float]) -> float:
    return np.mean([(t - p) ** 2 for t, p in zip(y_true, y_pred)])

def mae(y_true: list[float], y_pred: list[float]) -> float:
    return np.mean([abs(t - p) for t, p in zip(y_true, y_pred)])

def r_squared(y_true: list[float], y_pred: list[float]) -> float:
    ss_res = sum((t - p) ** 2 for t, p in zip(y_true, y_pred))
    ss_tot = sum((t - np.mean(y_true)) ** 2 for t in y_true)
    return 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
