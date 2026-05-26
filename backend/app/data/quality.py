from typing import List, Dict

def check_data_quality(data: List[Dict]) -> Dict:
    issues = []
    if not data:
        issues.append("No data available")
    return {
        "status": "ok" if not issues else "warning",
        "issues": issues,
        "record_count": len(data),
    }
