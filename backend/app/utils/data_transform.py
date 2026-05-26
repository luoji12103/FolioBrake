from typing import List, Dict, Any

def pivot_data(data: List[Dict], index: str, columns: str, values: str) -> Dict:
    result = {}
    for row in data:
        key = row[index]
        col = row[columns]
        val = row[values]
        if key not in result:
            result[key] = {}
        result[key][col] = val
    return result

def aggregate_data(data: List[Dict], group_by: str, agg_field: str, agg_func: str = "sum") -> List[Dict]:
    groups = {}
    for row in data:
        key = row[group_by]
        if key not in groups:
            groups[key] = []
        groups[key].append(row[agg_field])
    
    result = []
    for key, values in groups.items():
        if agg_func == "sum":
            result.append({group_by: key, agg_field: sum(values)})
        elif agg_func == "mean":
            result.append({group_by: key, agg_field: sum(values) / len(values)})
        elif agg_func == "count":
            result.append({group_by: key, agg_field: len(values)})
    return result
