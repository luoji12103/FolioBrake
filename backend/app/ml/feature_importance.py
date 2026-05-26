import numpy as np

def calculate_importance(features: list[list[float]], targets: list[float]) -> dict:
    if not features or not features[0]:
        return {}
    
    n_features = len(features[0])
    importance = {}
    
    for i in range(n_features):
        feature_values = [row[i] for row in features]
        correlation = abs(np.corrcoef(feature_values, targets)[0, 1])
        importance[f"feature_{i}"] = correlation if not np.isnan(correlation) else 0.0
    
    return importance
