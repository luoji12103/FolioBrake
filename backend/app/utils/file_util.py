import os

def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

def file_exists(path: str) -> bool:
    return os.path.isfile(path)

def read_file(path: str) -> str:
    with open(path, 'r') as f:
        return f.read()

def write_file(path: str, content: str):
    ensure_dir(os.path.dirname(path))
    with open(path, 'w') as f:
        f.write(content)
