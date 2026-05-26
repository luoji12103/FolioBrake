import csv
import io
import json

def import_csv(content: str) -> list:
    reader = csv.DictReader(io.StringIO(content))
    return list(reader)

def import_json(content: str) -> list:
    return json.loads(content)
