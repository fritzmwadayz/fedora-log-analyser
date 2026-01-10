"""Main REPL - Simplified version of existing code."""
'''
import subprocess, json
from collections import defaultdict
import datetime
import os
import sys
from typing import Dict, List, Optional
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import numpy as np

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

    def show_visualization(self, chart_type: str = "bar"):
        """Generate visualizations from analyzed data"""
        if not self.processed_data:
            print("No data analyzed. Use 'analyze' command first.")
            return
        
        print("Available visualizations:")
        print("  1. Priority distribution (pie)")
        print("  2. Domain distribution (bar)")
        print("  3. Monthly trends (line)")
        print("  4. Hourly distribution (histogram)")
        print("  5. Error heatmap (heatmap)")
        
        try:
            choice = input("Select visualization (1-5): ").strip()
            
            if choice == "1":
                self._plot_priority_distribution()
            elif choice == "2":
                self._plot_domain_distribution()
            elif choice == "3":
                self._plot_monthly_trends()
            elif choice == "4":
                self._plot_hourly_distribution()
            elif choice == "5":
                self._plot_error_heatmap()
            else:
                print("Invalid choice")
                
        except ImportError:
            print("Visualization libraries not installed.")
            print("Install with: pip install matplotlib seaborn")
        except Exception as e:
            print(f"Visualization error: {e}")
    
    def _plot_priority_distribution(self):
        """Create pie chart of log priorities"""
        # Aggregate priority data
        priority_totals = defaultdict(int)
        for month_data in self.processed_data.values():
            for domain_data in month_data.values():
                for priority, count in domain_data.items():
                    priority_totals[priority] += count
        
        if not priority_totals:
            print("No priority data available")
            return
        
        # Prepare data
        labels = list(priority_totals.keys())
        sizes = list(priority_totals.values())
        
        # Color mapping for priorities
        priority_colors = {
            "EMERGENCY": "#FF0000",
            "ALERT": "#FF4500",
            "CRITICAL": "#FF8C00",
            "ERROR": "#FFA500",
            "WARNING": "#FFFF00",
            "NOTICE": "#ADFF2F",
            "INFO": "#32CD32",
            "DEBUG": "#87CEEB"
        }
        
        colors = [priority_colors.get(p, "#999999") for p in labels]
        
        # Create plot
        plt.figure(figsize=(10, 8))
        patches, texts, autotexts = plt.pie(
            sizes, labels=labels, colors=colors, autopct='%1.1f%%',
            startangle=90, pctdistance=0.85
        )
        
        # Make percentage text white and bold
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        # Draw circle for donut chart
        centre_circle = plt.Circle((0, 0), 0.70, fc='white')
        fig = plt.gcf()
        fig.gca().add_artist(centre_circle)
        
        plt.title('Log Priority Distribution', fontsize=16, fontweight='bold')
        plt.axis('equal')  # Equal aspect ratio ensures pie is drawn as circle
        
        # Add legend
        plt.legend(patches, labels, loc="best", fontsize=10)
        
        plt.tight_layout()
        plt.show()
    
    def _plot_domain_distribution(self):
        """Create bar chart of log domains"""
        domain_totals = defaultdict(int)
        for month_data in self.processed_data.values():
            for domain, domain_data in month_data.items():
                domain_totals[domain] += sum(domain_data.values())
        
        if not domain_totals:
            print("No domain data available")
            return
        
        # Sort domains by count
        domains = sorted(domain_totals.items(), key=lambda x: x[1], reverse=True)
        domain_names = [d[0] for d in domains]
        counts = [d[1] for d in domains]
        
        plt.figure(figsize=(12, 6))
        
        # Create color gradient
        colors = plt.cm.viridis(np.linspace(0, 0.8, len(domain_names)))
        
        bars = plt.bar(domain_names, counts, color=colors, edgecolor='black')
        
        # Add count labels on bars
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                    f'{int(height)}', ha='center', va='bottom', fontsize=9)
        
        plt.xlabel('Domain', fontsize=12, fontweight='bold')
        plt.ylabel('Number of Log Entries', fontsize=12, fontweight='bold')
        plt.title('Log Distribution by Domain', fontsize=14, fontweight='bold')
        plt.xticks(rotation=45, ha='right')
        plt.grid(axis='y', alpha=0.3, linestyle='--')
        plt.tight_layout()
        plt.show()
    
    def _plot_monthly_trends(self):
        """Create line chart showing trends over months"""
        if not self.raw_logs:
            print("No raw log data available. Load logs first.")
            return
        
        # Extract month and error counts
        monthly_errors = defaultdict(int)
        monthly_total = defaultdict(int)
        
        for line in self.raw_logs[:5000]:  # Sample for performance
            try:
                log_entry = json.loads(line)
                priority_num = str(log_entry.get("PRIORITY", "6"))
                priority = self.PRIO_MAP.get(priority_num, "INFO")
                
                # Get month
                timestamp = log_entry.get("__realtime_timestamp")
                if timestamp:
                    dt = datetime.fromtimestamp(int(timestamp) / 1000000)
                    month = dt.strftime("%Y-%m")  # Year-Month for ordering
                    
                    monthly_total[month] += 1
                    if priority in ["ERROR", "CRITICAL", "ALERT", "EMERGENCY"]:
                        monthly_errors[month] += 1
                        
            except (json.JSONDecodeError, ValueError):
                continue
        
        if not monthly_total:
            print("No monthly data available")
            return
        
        # Sort months chronologically
        months = sorted(monthly_total.keys())
        totals = [monthly_total[m] for m in months]
        errors = [monthly_errors.get(m, 0) for m in months]
        
        # Calculate error rates
        error_rates = [(e/t)*100 if t > 0 else 0 for e, t in zip(errors, totals)]
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        
        # Plot 1: Total logs
        ax1.plot(months, totals, marker='o', linewidth=2, markersize=8, 
                color='blue', label='Total Logs')
        ax1.fill_between(months, totals, alpha=0.2, color='blue')
        ax1.set_xlabel('Month')
        ax1.set_ylabel('Total Log Entries')
        ax1.set_title('Monthly Log Volume', fontweight='bold')
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        # Plot 2: Error rate
        ax2.plot(months, error_rates, marker='s', linewidth=2, markersize=8,
                color='red', label='Error Rate')
        ax2.fill_between(months, error_rates, alpha=0.2, color='red')
        ax2.set_xlabel('Month')
        ax2.set_ylabel('Error Rate (%)')
        ax2.set_title('Monthly Error Rate', fontweight='bold')
        ax2.grid(True, alpha=0.3)
        ax2.legend()
        
        # Rotate x-axis labels
        for ax in [ax1, ax2]:
            plt.sca(ax)
            plt.xticks(rotation=45, ha='right')
        
        plt.tight_layout()
        plt.show()
    
    def _plot_hourly_distribution(self):
        """Show when logs occur throughout the day"""
        hourly_counts = defaultdict(int)
        
        for line in self.raw_logs[:10000]:  # Sample size
            try:
                log_entry = json.loads(line)
                timestamp = log_entry.get("__realtime_timestamp")
                if timestamp:
                    dt = datetime.fromtimestamp(int(timestamp) / 1000000)
                    hour = dt.hour
                    hourly_counts[hour] += 1
            except (json.JSONDecodeError, ValueError):
                continue
        
        if not hourly_counts:
            print("No hourly data available")
            return
        
        # Prepare data
        hours = list(range(24))
        counts = [hourly_counts.get(h, 0) for h in hours]
        
        plt.figure(figsize=(14, 6))
        
        # Create bar chart with gradient
        bars = plt.bar(hours, counts, color=plt.cm.coolwarm(np.linspace(0, 1, 24)))
        
        # Add hour labels
        hour_labels = [f"{h:02d}:00" for h in hours]
        plt.xticks(hours, hour_labels, rotation=45)
        
        # Color code by time of day
        for i, bar in enumerate(bars):
            if 6 <= i < 18:  # Daytime
                bar.set_alpha(0.8)
            else:  # Nighttime
                bar.set_edgecolor('white')
                bar.set_linewidth(1.5)
        
        plt.xlabel('Hour of Day', fontweight='bold')
        plt.ylabel('Number of Log Entries', fontweight='bold')
        plt.title('Log Activity by Hour of Day', fontweight='bold')
        plt.grid(axis='y', alpha=0.3, linestyle='--')
        
        # Add day/night shading
        plt.axvspan(6, 18, alpha=0.1, color='yellow', label='Daytime (6AM-6PM)')
        plt.axvspan(0, 6, alpha=0.1, color='blue', label='Night (12AM-6AM)')
        plt.axvspan(18, 24, alpha=0.1, color='blue')
        
        plt.legend()
        plt.tight_layout()
        plt.show()
    
    def _plot_error_heatmap(self):
        """Create heatmap of errors by domain and priority"""
        # Prepare data matrix
        domains = set()
        priorities = ["EMERGENCY", "ALERT", "CRITICAL", "ERROR", 
                     "WARNING", "NOTICE", "INFO", "DEBUG"]
        
        # Collect all domains
        for month_data in self.processed_data.values():
            domains.update(month_data.keys())
        
        domains = sorted(domains)
        
        # Create matrix
        matrix = np.zeros((len(domains), len(priorities)))
        
        for i, domain in enumerate(domains):
            for j, priority in enumerate(priorities):
                total = 0
                for month_data in self.processed_data.values():
                    if domain in month_data:
                        total += month_data[domain].get(priority, 0)
                matrix[i, j] = total
        
        # Log scale for better visualization
        matrix_log = np.log10(matrix + 1)  # +1 to avoid log(0)
        
        plt.figure(figsize=(14, 8))
        
        # Create heatmap
        sns.heatmap(matrix_log, 
                   xticklabels=priorities,
                   yticklabels=domains,
                   cmap='YlOrRd',
                   linewidths=0.5,
                   linecolor='gray',
                   cbar_kws={'label': 'Log10(Count + 1)'})
        
        plt.xlabel('Priority Level', fontweight='bold')
        plt.ylabel('Domain', fontweight='bold')
        plt.title('Log Distribution Heatmap (Domain × Priority)', fontweight='bold')
        
        # Add actual counts as text
        for i in range(len(domains)):
            for j in range(len(priorities)):
                count = int(matrix[i, j])
                if count > 0:
                    plt.text(j + 0.5, i + 0.5, str(count),
                            ha='center', va='center',
                            color='black' if count < np.median(matrix[matrix > 0]) else 'white',
                            fontsize=8)
        
        plt.tight_layout()
        plt.show()
    
    def export_chart(self, chart_type: str, filename: str):
        """Export chart to file"""
        # Save the last created chart
        if plt.get_fignums():
            plt.savefig(filename, dpi=300, bbox_inches='tight')
            print(f"Chart saved to {filename}")
        else:
            print("No chart to export. Create a visualization first.")

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
    
    # Add interactive table browser
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

    def add_advanced_features(self):
        """Demonstrate advanced features"""
        print("\n=== ADVANCED FEATURES ===")
        print("1. Anomaly detection")
        print("2. Alert rules")
        print("3. Export formats")
        print("4. Batch processing")
        print("5. Integration hooks")
        
        choice = input("\nSelect feature to demo: ").strip()
        
        if choice == "1":
            self._demo_anomaly_detection()
        elif choice == "2":
            self._demo_alert_rules()
        elif choice == "3":
            self._demo_export_formats()
        elif choice == "4":
            self._demo_batch_processing()
        elif choice == "5":
            self._demo_integration_hooks()
        else:
            print("Invalid choice")
    
    def _demo_anomaly_detection(self):
        """Demo simple anomaly detection"""
        if not self.processed_data:
            print("No data analyzed")
            return
        
        print("\n🔍 Anomaly Detection")
        print("-" * 40)
        
        # Detect unusual error spikes
        error_rates = []
        months = []
        
        for month, month_data in sorted(self.processed_data.items()):
            total = 0
            errors = 0
            
            for domain_data in month_data.values():
                for priority, count in domain_data.items():
                    total += count
                    if priority in ["ERROR", "CRITICAL", "ALERT", "EMERGENCY"]:
                        errors += count
            
            if total > 0:
                error_rate = (errors / total * 100)
                error_rates.append(error_rate)
                months.append(month)
        
        if len(error_rates) >= 3:
            # Simple anomaly: error rate > 2 standard deviations from mean
            mean = sum(error_rates) / len(error_rates)
            variance = sum((x - mean) ** 2 for x in error_rates) / len(error_rates)
            std_dev = variance ** 0.5
            
            print(f"Mean error rate: {mean:.1f}%")
            print(f"Std deviation: {std_dev:.1f}%")
            print("\nChecking for anomalies...")
            
            for month, rate in zip(months, error_rates):
                if rate > mean + (2 * std_dev):
                    print(f"⚠️  ANOMALY in {month}: {rate:.1f}% error rate "
                          f"(>{mean + (2*std_dev):.1f}%)")
                elif rate < mean - (2 * std_dev):
                    print(f"✅ LOW in {month}: {rate:.1f}% error rate "
                          f"(<{mean - (2*std_dev):.1f}%)")
                else:
                    print(f"  Normal in {month}: {rate:.1f}%")
        else:
            print("Need at least 3 months of data for anomaly detection")
    
    def _demo_alert_rules(self):
        """Demo alert rule system"""
        print("\n🚨 Alert Rule Configuration")
        print("-" * 40)
        
        # Define some alert rules
        alert_rules = [
            {
                "name": "High Error Rate",
                "condition": "error_rate > 5.0",
                "severity": "WARNING",
                "action": "print"
            },
            {
                "name": "Critical Errors",
                "condition": "critical_count > 10",
                "severity": "CRITICAL",
                "action": "print"
            },
            {
                "name": "Service Down",
                "condition": "process_errors.get('sshd', 0) > 5",
                "severity": "ERROR",
                "action": "email"
            }
        ]
        
        print("Configured Alert Rules:")
        for i, rule in enumerate(alert_rules, 1):
            print(f"{i}. [{rule['severity']}] {rule['name']}")
            print(f"   Condition: {rule['condition']}")
            print(f"   Action: {rule['action']}")
            print()
        
        # Simulate checking rules
        if self.processed_data:
            print("Simulating rule checks...")
            # Calculate metrics
            total = 0
            errors = 0
            critical_count = 0
            process_errors = defaultdict(int)
            
            for month_data in self.processed_data.values():
                for domain_data in month_data.values():
                    for priority, count in domain_data.items():
                        total += count
                        if priority in ["ERROR", "CRITICAL", "ALERT", "EMERGENCY"]:
                            errors += count
                        if priority in ["CRITICAL", "ALERT", "EMERGENCY"]:
                            critical_count += count
            
            error_rate = (errors / total * 100) if total > 0 else 0
            
            print(f"\nCurrent metrics:")
            print(f"  Error rate: {error_rate:.1f}%")
            print(f"  Critical count: {critical_count}")
            
            # Check rules
            if error_rate > 5.0:
                print("⚠️  Alert: High Error Rate detected!")
            if critical_count > 10:
                print("🚨 Alert: Critical Errors detected!")
    
    def _demo_export_formats(self):
        """Demo multiple export formats"""
        if not self.processed_data:
            print("No data to export")
            return
        
        print("\n📤 Export Formats")
        print("-" * 40)
        print("1. JSON (structured data)")
        print("2. CSV (spreadsheet)")
        print("3. HTML (web page)")
        print("4. Markdown (documentation)")
        
        choice = input("\nSelect format: ").strip()
        
        if choice == "1":
            self._export_json()
        elif choice == "2":
            self._export_csv()
        elif choice == "3":
            self._export_html()
        elif choice == "4":
            self._export_markdown()
        else:
            print("Invalid choice")
    
    def _export_json(self):
        """Export to JSON format"""
        import json
        from datetime import datetime
        
        export_data = {
            "metadata": {
                "export_date": datetime.now().isoformat(),
                "total_months": len(self.processed_data),
                "total_domains": sum(len(v) for v in self.processed_data.values())
            },
            "data": {
                month: {
                    domain: dict(counts)
                    for domain, counts in month_data.items()
                }
                for month, month_data in self.processed_data.items()
            }
        }
        
        filename = f"log_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        print(f"✅ Exported to {filename}")
    
    def _export_csv(self):
        """Export to CSV format"""
        import csv
        from datetime import datetime
        
        filename = f"log_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Month', 'Domain', 'Priority', 'Count'])
            
            for month, month_data in self.processed_data.items():
                for domain, domain_data in month_data.items():
                    for priority, count in domain_data.items():
                        writer.writerow([month, domain, priority, count])
        
        print(f"✅ Exported to {filename}")
    
    def _export_html(self):
        """Export to HTML format"""
        from datetime import datetime
        
        filename = f"log_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Log Analysis Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #4CAF50; color: white; }}
                tr:nth-child(even) {{ background-color: #f2f2f2; }}
                .critical {{ color: red; font-weight: bold; }}
                .error {{ color: orange; }}
                .warning {{ color: #ffcc00; }}
            </style>
        </head>
        <body>
            <h1>Log Analysis Report</h1>
            <p>Generated: {timestamp}</p>
            
            <h2>Summary</h2>
            <table>
                <tr>
                    <th>Month</th>
                    <th>Domain</th>
                    <th>Priority</th>
                    <th>Count</th>
                </tr>
                {rows}
            </table>
        </body>
        </html>
        """
        
        rows = []
        for month, month_data in self.processed_data.items():
            for domain, domain_data in month_data.items():
                for priority, count in domain_data.items():
                    priority_class = ""
                    if priority in ["CRITICAL", "ALERT", "EMERGENCY"]:
                        priority_class = "critical"
                    elif priority == "ERROR":
                        priority_class = "error"
                    elif priority == "WARNING":
                        priority_class = "warning"
                    
                    rows.append(f"""
                    <tr>
                        <td>{month}</td>
                        <td>{domain}</td>
                        <td class="{priority_class}">{priority}</td>
                        <td>{count}</td>
                    </tr>
                    """)
        
        html_content = html_template.format(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            rows="\n".join(rows)
        )
        
        with open(filename, 'w') as f:
            f.write(html_content)
        
        print(f"✅ Exported to {filename}")
        print(f"Open with: firefox {filename}  # or your browser")
    
    def _export_markdown(self):
        """Export to Markdown format"""
        from datetime import datetime
        
        filename = f"log_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        with open(filename, 'w') as f:
            f.write(f"# Log Analysis Report\n\n")
            f.write(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
            
            f.write("## Summary by Month\n\n")
            f.write("| Month | Domain | Priority | Count |\n")
            f.write("|-------|--------|----------|-------|\n")
            
            for month, month_data in self.processed_data.items():
                for domain, domain_data in month_data.items():
                    for priority, count in domain_data.items():
                        # Add emphasis for high priority
                        if priority in ["CRITICAL", "ALERT", "EMERGENCY"]:
                            priority = f"**{priority}**"
                        elif priority == "ERROR":
                            priority = f"*{priority}*"
                        
                        f.write(f"| {month} | {domain} | {priority} | {count} |\n")
        
        print(f"✅ Exported to {filename}")
    
    def _demo_batch_processing(self):
        """Demo batch processing capabilities"""
        print("\n⚡ Batch Processing Demo")
        print("-" * 40)
        
        # Simulate processing multiple time ranges
        time_ranges = [
            ("1 hour ago", "now"),
            ("yesterday", "today"),
            ("1 week ago", "now"),
        ]
        
        print("Processing multiple time ranges...")
        
        for since, until in time_ranges:
            print(f"\nProcessing: {since} to {until}")
            # In a real implementation, you would actually load these logs
            # For demo, just show what would happen
            print(f"  Would load logs from {since} to {until}")
            print(f"  Would analyze and store results")
        
        print("\n✅ Batch processing complete")
        print("All results would be aggregated and compared")
    
    def _demo_integration_hooks(self):
        """Demo integration with other systems"""
        print("\n🔗 Integration Hooks Demo")
        print("-" * 40)
        
        print("Available integrations:")
        print("1. Send alerts to Slack")
        print("2. Push metrics to Prometheus")
        print("3. Create JIRA tickets for critical errors")
        print("4. Send email reports")
        print("5. Webhook notifications")
        
        print("\nExample webhook payload:")
        webhook_example = {
            "event": "high_error_rate",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "error_rate": 7.5,
                "critical_count": 3,
                "affected_domains": ["NETWORK", "SECURITY"]
            }
        }
        
        import json
        print(json.dumps(webhook_example, indent=2))
        
        print("\nTo implement:")
        print("1. Define webhook URLs in config")
        print("2. Create payload templates")
        print("3. Add retry logic for failed deliveries")
        print("4. Add rate limiting")

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
            elif cmd_input.lower().startswith('visualize') or cmd_input.lower().startswith('viz'):
                analyzer.show_visualization()

            elif cmd_input.lower().startswith('table'):
                parts = cmd_input.split()
                table_type = parts[1] if len(parts) > 1 else "summary"
                limit = int(parts[2]) if len(parts) > 2 else 20
                analyzer.show_table(table_type, limit)

            elif cmd_input.lower() == 'browse':
                analyzer.browse_table()

            elif cmd_input.lower() == 'advanced':
                analyzer.add_advanced_features()

            elif cmd_input.lower() == 'tui':
                print("Launching TUI...")
                # Launch the TUI in a subprocess
                import subprocess
                subprocess.run([sys.executable, "logalyzer_tui.py"])

            elif cmd_input.lower().startswith('export'):
                parts = cmd_input.split()
                if len(parts) >= 2:
                    if parts[1] == 'json':
                        analyzer._export_json()
                    elif parts[1] == 'csv':
                        analyzer._export_csv()
                    elif parts[1] == 'html':
                        analyzer._export_html()
                    elif parts[1] == 'markdown':
                        analyzer._export_markdown()
                    else:
                        print("Unknown export format. Use: json, csv, html, markdown")
                else:
                    print("Usage: export <format>")
                    
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
'''