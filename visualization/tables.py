from collections import defaultdict
from datetime import datetime
import json

# Import detection for rich/tabulate
try:
    from tabulate import tabulate
    TABULATE_AVAILABLE = True
except ImportError:
    TABULATE_AVAILABLE = False

try:
    from rich.table import Table as RichTable
    from rich.console import Console as RichConsole
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

def show_table(self, table_type: str = "summary", limit: int = 20):
    """Display data in tabular format"""
    if not self.processed_data:
        print("No data analyzed. Use 'analyze' command first.")
        return
    
    table_type = table_type.lower()
    
    if table_type == "summary":
        self._show_summary_table(limit)
    elif table_type == "detailed":
        self._show_detailed_table(limit)
    elif table_type == "errors":
        self._show_errors_table(limit)
    elif table_type == "domains":
        self._show_domains_table(limit)
    else:
        print(f"Unknown table type: {table_type}")
        print("Available: summary, detailed, errors, domains")

def _show_summary_table(self, limit: int = 20):
    """Show summary table"""
    # Aggregate data
    summary_data = []
    
    for month, month_data in sorted(self.processed_data.items()):
        month_total = 0
        month_errors = 0
        
        for domain_data in month_data.values():
            for priority, count in domain_data.items():
                month_total += count
                if priority in ["ERROR", "CRITICAL", "ALERT", "EMERGENCY"]:
                    month_errors += count
        
        error_rate = (month_errors / month_total * 100) if month_total > 0 else 0
        
        summary_data.append([
            month,
            month_total,
            month_errors,
            f"{error_rate:.1f}%",
            len(month_data)  # Number of domains
        ])
    
    if RICH_AVAILABLE:
        console = RichConsole()
        table = RichTable(title="Log Analysis Summary", box=box.ROUNDED)
        
        table.add_column("Month", style="cyan", no_wrap=True)
        table.add_column("Total", justify="right", style="green")
        table.add_column("Errors", justify="right", style="red")
        table.add_column("Error %", justify="right", style="yellow")
        table.add_column("Domains", justify="right", style="blue")
        
        for row in summary_data[:limit]:
            table.add_row(*[str(x) for x in row])
        
        console.print(table)
        
    elif TABULATE_AVAILABLE:
        headers = ["Month", "Total Logs", "Errors", "Error %", "Domains"]
        print(tabulate(summary_data[:limit], headers=headers, 
                      tablefmt="grid", floatfmt=".1f"))
    else:
        # Fallback to basic formatting
        print("Month       Total  Errors  Error%  Domains")
        print("-" * 45)
        for row in summary_data[:limit]:
            print(f"{row[0]:10} {row[1]:6} {row[2]:7} {row[3]:7} {row[4]:8}")

def _show_detailed_table(self, limit: int = 20):
    """Show detailed table with all data"""
    detailed_data = []
    
    for month, month_data in sorted(self.processed_data.items()):
        for domain, domain_data in sorted(month_data.items()):
            for priority, count in sorted(domain_data.items()):
                if count > 0:
                    detailed_data.append([
                        month, domain, priority, count
                    ])
    
    if RICH_AVAILABLE:
        console = RichConsole()
        table = RichTable(title="Detailed Log Analysis", box=box.ROUNDED)
        
        table.add_column("Month", style="cyan")
        table.add_column("Domain", style="magenta")
        
        # Color-coded priority column
        def get_priority_style(priority):
            if priority in ["EMERGENCY", "ALERT", "CRITICAL"]:
                return "bold red"
            elif priority == "ERROR":
                return "red"
            elif priority == "WARNING":
                return "yellow"
            elif priority == "NOTICE":
                return "blue"
            else:
                return "green"
        
        table.add_column("Priority", style=get_priority_style)
        table.add_column("Count", justify="right", style="bold")
        
        for month, domain, priority, count in detailed_data[:limit]:
            table.add_row(month, domain, priority, str(count))
        
        console.print(table)
        
    elif TABULATE_AVAILABLE:
        headers = ["Month", "Domain", "Priority", "Count"]
        print(tabulate(detailed_data[:limit], headers=headers, 
                      tablefmt="grid"))
    else:
        print("Month  Domain              Priority    Count")
        print("-" * 45)
        for row in detailed_data[:limit]:
            print(f"{row[0]:6} {row[1]:18} {row[2]:10} {row[3]:5}")

def _show_errors_table(self, limit: int = 20):
    """Show only error-related logs"""
    if not self.data_loaded:
        print("No logs loaded. Use 'load' command first.")
        return
    
    error_data = []
    
    for line in self.raw_logs[:500]:  # Limit for performance
        try:
            log_entry = json.loads(line)
            priority_num = str(log_entry.get("PRIORITY", "6"))
            priority = self.PRIO_MAP.get(priority_num, "INFO")
            
            if priority in ["ERROR", "CRITICAL", "ALERT", "EMERGENCY"]:
                process = log_entry.get("SYSLOG_IDENTIFIER", "unknown")
                message = log_entry.get("MESSAGE", "")[:60]
                
                timestamp = log_entry.get("__realtime_timestamp")
                if timestamp:
                    dt = datetime.fromtimestamp(int(timestamp) / 1000000)
                    time_str = dt.strftime("%H:%M:%S")
                else:
                    time_str = "Unknown"
                
                error_data.append([
                    time_str, process, priority, message
                ])
                
                if len(error_data) >= limit:
                    break
                    
        except (json.JSONDecodeError, ValueError):
            continue
    
    if not error_data:
        print("No errors found in logs")
        return
    
    if RICH_AVAILABLE:
        console = RichConsole()
        table = RichTable(title=f"Recent Errors (Last {len(error_data)})", box=box.ROUNDED)
        
        table.add_column("Time", style="dim")
        table.add_column("Process", style="cyan")
        table.add_column("Priority", style="red")
        table.add_column("Message", style="white")
        
        for time_str, process, priority, message in error_data:
            table.add_row(time_str, process, priority, message)
        
        console.print(table)
        
    elif TABULATE_AVAILABLE:
        headers = ["Time", "Process", "Priority", "Message"]
        print(tabulate(error_data, headers=headers, tablefmt="grid"))
    else:
        print("Time     Process              Priority  Message")
        print("-" * 70)
        for row in error_data:
            print(f"{row[0]:8} {row[1]:20} {row[2]:9} {row[3]}")

def _show_domains_table(self, limit: int = 20):
    """Show domain statistics"""
    domain_stats = defaultdict(lambda: defaultdict(int))
    
    for month_data in self.processed_data.values():
        for domain, domain_data in month_data.items():
            for priority, count in domain_data.items():
                domain_stats[domain]['total'] += count
                if priority in ["ERROR", "CRITICAL", "ALERT", "EMERGENCY"]:
                    domain_stats[domain]['errors'] += count
    
    # Convert to list and sort
    table_data = []
    for domain, stats in sorted(domain_stats.items()):
        total = stats['total']
        errors = stats['errors']
        error_rate = (errors / total * 100) if total > 0 else 0
        
        table_data.append([
            domain, total, errors, f"{error_rate:.1f}%"
        ])
    
    if RICH_AVAILABLE:
        console = RichConsole()
        table = RichTable(title="Domain Statistics", box=box.ROUNDED)
        
        table.add_column("Domain", style="cyan")
        table.add_column("Total", justify="right", style="green")
        table.add_column("Errors", justify="right", style="red")
        table.add_column("Error %", justify="right", style="yellow")
        
        for domain, total, errors, error_rate in table_data[:limit]:
            table.add_row(domain, str(total), str(errors), error_rate)
        
        console.print(table)
        
    elif TABULATE_AVAILABLE:
        headers = ["Domain", "Total", "Errors", "Error %"]
        print(tabulate(table_data[:limit], headers=headers, 
                      tablefmt="grid", floatfmt=".1f"))
    else:
        print("Domain              Total  Errors  Error%")
        print("-" * 40)
        for row in table_data[:limit]:
            print(f"{row[0]:18} {row[1]:6} {row[2]:7} {row[3]:7}")

def browse_table(self):
    """Interactive table browser"""
    if not self.processed_data:
        print("No data analyzed. Use 'analyze' command first.")
        return
    
    current_page = 0
    page_size = 10
    
    # Get all data for paging
    all_data = []
    for month, month_data in sorted(self.processed_data.items()):
        for domain, domain_data in sorted(month_data.items()):
            for priority, count in sorted(domain_data.items()):
                if count > 0:
                    all_data.append([month, domain, priority, count])
    
    total_pages = (len(all_data) + page_size - 1) // page_size
    
    while True:
        start_idx = current_page * page_size
        end_idx = start_idx + page_size
        page_data = all_data[start_idx:end_idx]
        
        # Display current page
        print(f"\nPage {current_page + 1}/{total_pages} "
              f"({len(all_data)} total entries)")
        
        if RICH_AVAILABLE or TABULATE_AVAILABLE:
            self._show_detailed_table_data(page_data)
        else:
            print("Month  Domain              Priority    Count")
            print("-" * 45)
            for month, domain, priority, count in page_data:
                print(f"{month:6} {domain:18} {priority:10} {count:5}")
        
        # Navigation
        print("\nNavigation: [n]ext, [p]revious, [j]ump to page, [q]uit")
        cmd = input("Command: ").strip().lower()
        
        if cmd == 'n' and current_page < total_pages - 1:
            current_page += 1
        elif cmd == 'p' and current_page > 0:
            current_page -= 1
        elif cmd.startswith('j'):
            try:
                page = int(cmd.split()[1]) - 1
                if 0 <= page < total_pages:
                    current_page = page
            except (ValueError, IndexError):
                print("Invalid page number")
        elif cmd == 'q':
            break

def _show_detailed_table_data(self, data):
    """Helper to show table data with available formatter"""
    if RICH_AVAILABLE:
        console = RichConsole()
        table = RichTable(box=box.SIMPLE)
        
        table.add_column("Month", style="cyan")
        table.add_column("Domain", style="magenta")
        table.add_column("Priority")
        table.add_column("Count", justify="right")
        
        for month, domain, priority, count in data:
            table.add_row(month, domain, priority, str(count))
        
        console.print(table)
    elif TABULATE_AVAILABLE:
        headers = ["Month", "Domain", "Priority", "Count"]
        print(tabulate(data, headers=headers, tablefmt="simple"))