import csv
import io
import json

def export_csv(data: list, filename: str = "export.csv"):
    output = io.StringIO()
    if data:
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    return output.getvalue()

def export_json(data: list, filename: str = "export.json"):
    return json.dumps(data, indent=2)
