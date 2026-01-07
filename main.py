import subprocess, json
from collections import defaultdict
import datetime
import os
import sys
from typing import Dict, List, Optional

class LogAnalyzerREPL:
    def __init__(self):
        self.PRIO_MAP = {
            "0": "EMERGENCY", "1": "ALERT", "2": "CRITICAL", "3": "ERROR",
            "4": "WARNING", "5": "NOTICE", "6": "INFO", "7": "DEBUG"
        }
        
        self.DOMAIN_MAP = {
            "KERNEL": {"kernel"},
            "BOOT": {"systemd", "dracut", "dracut-cmdline", "systemd-modules-load", "systemd-fsck"},
            "NETWORK": {"NetworkManager", "wpa_supplicant", "ModemManager", "avahi-daemon", "chronyd"},
            "AUDIO": {"pipewire", "wireplumber", "alsactl"},
            "SECURITY": {"auditd", "audit", "polkitd", "setroubleshoot", "sudo"},
            "PACKAGE_MGMT": {"dnf", "dnf5", "dnf5daemon-server", "PackageKit", "fwupd"},
            "CRASH_HANDLING": {"abrt-server", "abrtd", "abrt-dump-journal-core", "systemd-coredump"},
            "SCHEDULERS": {"crond", "CROND", "atd", "anacron"},
            "DESKTOP": {"xfce4-terminal", "dolphin", "vlc", "chrome", "brave-browser-stable"},
        }
        
        self.data_loaded = False
        self.raw_logs = []
        self.processed_data = None
        self.line_limit = 10000  # Default limit
        
    def classify_process(self, proc: str) -> str:
        """Classify process into domain"""
        if not proc or proc == "unknown":
            return "MISC"
            
        for domain, names in self.DOMAIN_MAP.items():
            if proc in names:
                return domain

        if proc.startswith("systemd"):
            return "BOOT"

        return "MISC"
    
    def load_logs(self, limit: Optional[int] = None, since: str = None, until: str = None):
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
                return False
                
            self.raw_logs = output.stdout.splitlines()
            self.data_loaded = True
            print(f"Loaded {len(self.raw_logs)} log entries")
            return True
            
        except subprocess.TimeoutExpired:
            print("Timeout loading logs. Try with a smaller limit.")
            return False
        except Exception as e:
            print(f"Error: {e}")
            return False
    
    def analyze_logs(self):
        """Process and analyze loaded logs"""
        if not self.data_loaded:
            print("No logs loaded. Use 'load' command first.")
            return None
            
        month_counts = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
        total_lines = len(self.raw_logs)
        processed = 0
        
        print(f"Analyzing {total_lines} log entries...")
        
        for line in self.raw_logs:
            processed += 1
            if processed % 5000 == 0:
                print(f"  Processed {processed}/{total_lines} entries...")
                
            try:
                log_entry = json.loads(line)
                
                # Extract process name
                process = log_entry.get("SYSLOG_IDENTIFIER", "unknown")
                if not process or process == "unknown":
                    process = log_entry.get("_COMM", "unknown")
                
                # Extract priority
                priority_num = str(log_entry.get("PRIORITY", "6"))
                priority = self.PRIO_MAP.get(priority_num, "INFO")
                
                # Extract timestamp and month
                timestamp = log_entry.get("__realtime_timestamp")
                if timestamp:
                    dt = datetime.datetime.fromtimestamp(int(timestamp) / 1000000)
                    month = dt.strftime("%b")
                else:
                    month = "Unknown"
                
                # Classify and count
                domain = self.classify_process(process)
                month_counts[month][domain][priority] += 1
                
            except (json.JSONDecodeError, KeyError, ValueError):
                continue
        
        self.processed_data = month_counts
        print(f"Analysis complete. Processed {processed} entries.")
        return month_counts
    
    def show_summary(self):
        """Show summary of analyzed data"""
        if not self.processed_data:
            print("No data analyzed. Use 'analyze' command first.")
            return
        
        print("\n=== LOG ANALYSIS SUMMARY ===")
        for month in sorted(self.processed_data.keys()):
            print(f"\n{month}:")
            for domain in sorted(self.processed_data[month].keys()):
                total = sum(self.processed_data[month][domain].values())
                print(f"  {domain}: {total} entries")
    
    def show_detailed(self, month: Optional[str] = None, domain: Optional[str] = None):
        """Show detailed breakdown"""
        if not self.processed_data:
            print("No data analyzed. Use 'analyze' command first.")
            return
        
        priority_order = ["EMERGENCY", "ALERT", "CRITICAL", "ERROR", 
                         "WARNING", "NOTICE", "INFO", "DEBUG"]
        
        if month:
            months_to_show = [month] if month in self.processed_data else []
        else:
            months_to_show = sorted(self.processed_data.keys())
        
        for m in months_to_show:
            print(f"\n=== {m} ===")
            domains = [domain] if domain and domain in self.processed_data[m] else sorted(self.processed_data[m].keys())
            
            for d in domains:
                print(f"\n{d}:")
                for prio in priority_order:
                    count = self.processed_data[m][d].get(prio, 0)
                    if count > 0:
                        print(f"  {prio}: {count}")
    
    def search_logs(self, keyword: str, level: str = None):
        """Search logs for specific keyword"""
        if not self.data_loaded:
            print("No logs loaded. Use 'load' command first.")
            return
        
        print(f"\nSearching for '{keyword}' in logs...")
        results = []
        
        for line in self.raw_logs[:100]:  # Limit search to first 100 for performance
            try:
                log_entry = json.loads(line)
                message = log_entry.get("MESSAGE", "")
                
                if keyword.lower() in message.lower():
                    # Check priority filter
                    if level:
                        priority_num = str(log_entry.get("PRIORITY", "6"))
                        priority = self.PRIO_MAP.get(priority_num, "INFO")
                        if priority != level.upper():
                            continue
                    
                    # Format result
                    process = log_entry.get("SYSLOG_IDENTIFIER", log_entry.get("_COMM", "unknown"))
                    timestamp = log_entry.get("__realtime_timestamp")
                    if timestamp:
                        dt = datetime.datetime.fromtimestamp(int(timestamp) / 1000000)
                        time_str = dt.strftime("%H:%M:%S")
                    else:
                        time_str = "Unknown"
                    
                    results.append(f"[{time_str}] {process}: {message[:80]}...")
                    
                    if len(results) >= 10:  # Limit results
                        break
                        
            except (json.JSONDecodeError, KeyError, ValueError):
                continue
        
        if results:
            print(f"Found {len(results)} matching entries:")
            for r in results:
                print(f"  {r}")
        else:
            print("No matches found.")
    
    def show_help(self):
        """Show available commands"""
        help_text = """
=== Log Analyzer REPL Commands ===

  load [limit] [since] [until]  - Load logs (e.g., 'load 5000', 'load since="1 hour ago"')
  analyze                       - Analyze loaded logs
  summary                       - Show analysis summary
  detailed [month] [domain]     - Show detailed breakdown
  search <keyword> [level]      - Search logs (e.g., 'search error', 'search failed ERROR')
  stats                         - Show statistics
  help                          - Show this help
  quit / q                      - Exit the program
  
Examples:
  load 10000                    # Load last 10,000 entries
  load since="yesterday"        # Load since yesterday
  analyze                       # Process loaded logs
  summary                       # Show summary
  detailed                      # Show all details
  detailed Jan NETWORK          # Show January network logs
  search authentication         # Search for authentication
  search failed ERROR           # Search 'failed' at ERROR level
  
Filters available for 'load':
  since="2024-01-01"           # From date
  until="2024-01-02"           # Until date
  since="1 hour ago"           # Relative time
  since="yesterday"            # Relative time
        """
        print(help_text)

def main():
    analyzer = LogAnalyzerREPL()
    
    print("""
╔══════════════════════════════════════════╗
║        Journal Log Analyzer REPL         ║
║          Interactive Log Analysis        ║
╚══════════════════════════════════════════╝
    """)
    
    while True:
        try:
            cmd_input = input("\nlog-analyzer> ").strip()
            
            if cmd_input.lower() in ['quit', 'q', 'exit']:
                print("Goodbye!")
                break
                
            elif cmd_input.lower() == 'help' or cmd_input == '?':
                analyzer.show_help()
                
            elif cmd_input.lower().startswith('load'):
                # Parse load command with parameters
                parts = cmd_input.split()
                limit = None
                since = None
                until = None
                
                for part in parts[1:]:
                    if part.isdigit():
                        limit = int(part)
                    elif part.startswith('since='):
                        since = part.split('=')[1].strip('"\'')
                    elif part.startswith('until='):
                        until = part.split('=')[1].strip('"\'')
                
                analyzer.load_logs(limit, since, until)
                
            elif cmd_input.lower() == 'analyze':
                analyzer.analyze_logs()
                
            elif cmd_input.lower() == 'summary':
                analyzer.show_summary()
                
            elif cmd_input.lower().startswith('detailed'):
                parts = cmd_input.split()
                month = parts[1] if len(parts) > 1 else None
                domain = parts[2] if len(parts) > 2 else None
                analyzer.show_detailed(month, domain)
                
            elif cmd_input.lower().startswith('search'):
                parts = cmd_input.split()
                if len(parts) < 2:
                    print("Usage: search <keyword> [level]")
                else:
                    keyword = parts[1]
                    level = parts[2] if len(parts) > 2 else None
                    analyzer.search_logs(keyword, level)
                    
            elif cmd_input.lower() == 'stats':
                if analyzer.data_loaded:
                    print(f"Logs loaded: {len(analyzer.raw_logs)} entries")
                    if analyzer.processed_data:
                        total_months = len(analyzer.processed_data)
                        total_domains = sum(len(v) for v in analyzer.processed_data.values())
                        print(f"Analysis complete: {total_months} months, {total_domains} domains")
                    else:
                        print("Data not analyzed yet.")
                else:
                    print("No logs loaded.")
                    
            elif cmd_input == '':
                continue
                
            else:
                print(f"Unknown command: {cmd_input}")
                print("Type 'help' for available commands.")
                
        except KeyboardInterrupt:
            print("\n\nUse 'quit' or 'q' to exit.")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()