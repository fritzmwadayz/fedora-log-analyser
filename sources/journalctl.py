import subprocess
import json
from typing import Optional, List

def load_journal_logs(limit: Optional[int] = None, since: str = None, until: str = None) -> List[str]:
    """Load logs from journalctl with optional filters"""
    cmd = ["journalctl", "--output=json", "--no-pager"]
    
    if limit:
        cmd.extend(["-n", str(limit)])
    if since:
        cmd.extend(["--since", since])
    if until:
        cmd.extend(["--until", until])
        
    print(f"Loading logs with command: {' '.join(cmd)}")
    
    try:
        output = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30  # Timeout after 30 seconds
        )
        
        if output.returncode != 0:
            print(f"Error loading logs: {output.stderr}")
            return []
            
        logs = output.stdout.splitlines()
        print(f"Loaded {len(logs)} log entries")
        return logs
        
    except subprocess.TimeoutExpired:
        print("Timeout loading logs. Try with a smaller limit.")
        return []
    except Exception as e:
        print(f"Error: {e}")
        return []