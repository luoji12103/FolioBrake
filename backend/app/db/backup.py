import subprocess
import os
from datetime import datetime

def backup_database(output_dir: str = "/root/backups"):
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"guardian_{timestamp}.sql"
    filepath = os.path.join(output_dir, filename)
    
    subprocess.run([
        "pg_dump",
        "-h", "postgres",
        "-U", "guardian",
        "-d", "guardian",
        "-f", filepath
    ], check=True)
    
    return filepath
