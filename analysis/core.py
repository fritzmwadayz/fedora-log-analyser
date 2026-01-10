import json
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional, DefaultDict, Any
from sources.journalctl import load_journal_logs
from config.defaults import PRIO_MAP, DOMAIN_MAP

class LogAnalyzer:
    def __init__(self):
        self.PRIO_MAP = PRIO_MAP
        self.DOMAIN_MAP = DOMAIN_MAP
        
        self.data_loaded = False
        self.raw_logs = []
        self.processed_data = None
        self.line_limit = 10000
    
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
    
    def load_logs(self, limit: Optional[int] = None, since: str = None, until: str = None) -> bool:
        """Load logs from journalctl with optional filters"""
        self.raw_logs = load_journal_logs(limit, since, until)
        self.data_loaded = bool(self.raw_logs)
        return self.data_loaded
    
    def analyze_logs(self) -> Optional[Dict]:
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
                    dt = datetime.fromtimestamp(int(timestamp) / 1000000)
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
                        dt = datetime.fromtimestamp(int(timestamp) / 1000000)
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
    
    def show_stats(self):
        """Show basic statistics"""
        if self.data_loaded:
            print(f"Logs loaded: {len(self.raw_logs)} entries")
            if self.processed_data:
                total_months = len(self.processed_data)
                total_domains = sum(len(v) for v in self.processed_data.values())
                print(f"Analysis complete: {total_months} months, {total_domains} domains")
            else:
                print("Data not analyzed yet.")
        else:
            print("No logs loaded.")
    
    # Import visualization methods
    from visualization.charts import (
        show_visualization as show_visualization,
        _plot_priority_distribution as _plot_priority_distribution,
        _plot_domain_distribution as _plot_domain_distribution,
        _plot_monthly_trends as _plot_monthly_trends,
        _plot_hourly_distribution as _plot_hourly_distribution,
        _plot_error_heatmap as _plot_error_heatmap
    )
    
    # Import table methods
    from visualization.tables import (
        show_table as show_table,
        _show_summary_table as _show_summary_table,
        _show_detailed_table as _show_detailed_table,
        _show_errors_table as _show_errors_table,
        _show_domains_table as _show_domains_table,
        browse_table as browse_table,
        _show_detailed_table_data as _show_detailed_table_data
    )
    
    # Import advanced features
    from analysis.anomalies import add_advanced_features as add_advanced_features
    from data.export import export_data as export_data
    
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
  visualize / viz               - Generate visualizations
  table [type] [limit]          - Display data in tables
  browse                        - Interactive table browser
  advanced                      - Advanced features demo
  export <format>               - Export data (json, csv, html, markdown)
  help                          - Show this help
  quit / q                      - Exit the program
  tui                           - Launch tui window
  
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