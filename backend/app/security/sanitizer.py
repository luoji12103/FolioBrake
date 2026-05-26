import re

def sanitize_string(value: str) -> str:
    if not isinstance(value, str):
        return value
    value = re.sub(r'<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>', '', value, flags=re.IGNORECASE)
    return value.strip()

def validate_symbol(symbol: str) -> bool:
    return bool(re.match(r'^[0-9]{6}$', symbol))
