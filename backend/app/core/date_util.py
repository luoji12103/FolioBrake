from datetime import datetime, date

def parse_date(date_str: str) -> date:
    for fmt in ("%Y-%m-%d", "%Y%m%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Invalid date format: {date_str}")

def format_date(d: date, fmt: str = "%Y-%m-%d") -> str:
    return d.strftime(fmt)
