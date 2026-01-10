"""
logalyzer_tui.py - TUI interface for log analyzer
"""

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Tree, DataTable, Static, Label
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.screen import Screen
from textual.reactive import reactive
from textual import events
from datetime import datetime
import json
import subprocess
from collections import defaultdict
from typing import Dict, List, Optional

# Import your existing analyzer (simplified version)
class LogAnalyzerTUI:
    """Lightweight analyzer for TUI"""
    
    PRIO_MAP = {
        "0": "EMERGENCY", "1": "ALERT", "2": "CRITICAL", "3": "ERROR",
        "4": "WARNING", "5": "NOTICE", "6": "INFO", "7": "DEBUG"
    }
    
    def __init__(self):
        self.logs = []
        self.summary = {}
    
    def load_logs(self, limit: int = 1000) -> bool:
        """Load logs for TUI display"""
        try:
            cmd = ["journalctl", "--output=json", "--no-pager", "-n", str(limit)]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                self.logs = result.stdout.splitlines()[:500]  # Limit for TUI
                return True
        except Exception:
            pass
        return False
    
    def get_summary(self) -> Dict:
        """Get quick summary for TUI"""
        summary = defaultdict(lambda: defaultdict(int))
        
        for line in self.logs[:200]:  # Sample for performance
            try:
                entry = json.loads(line)
                priority = self.PRIO_MAP.get(str(entry.get("PRIORITY", "6")), "INFO")
                
                # Simple domain detection
                process = entry.get("SYSLOG_IDENTIFIER", "unknown")
                if process == "kernel":
                    domain = "KERNEL"
                elif "systemd" in process:
                    domain = "SYSTEMD"
                elif "Network" in process or "wpa" in process:
                    domain = "NETWORK"
                else:
                    domain = "OTHER"
                
                summary[domain][priority] += 1
                
            except json.JSONDecodeError:
                continue
        
        return dict(summary)

# TUI Application
class DashboardScreen(Screen):
    """Main dashboard screen"""
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Horizontal(
                Vertical(
                    Static("📊 Log Summary", classes="widget-title"),
                    Static(id="summary-widget", classes="widget"),
                    classes="widget-container"
                ),
                Vertical(
                    Static("🚨 Recent Errors", classes="widget-title"),
                    Static(id="errors-widget", classes="widget"),
                    classes="widget-container"
                ),
            ),
            Horizontal(
                Vertical(
                    Static("📈 Priority Distribution", classes="widget-title"),
                    Static(id="priority-widget", classes="widget"),
                    classes="widget-container"
                ),
                Vertical(
                    Static("🏷️  Domains", classes="widget-title"),
                    Static(id="domains-widget", classes="widget"),
                    classes="widget-container"
                ),
            ),
        )
        yield Footer()
    
    def on_mount(self) -> None:
        """Load data when screen mounts"""
        self.analyzer = LogAnalyzerTUI()
        if self.analyzer.load_logs(1000):
            self.update_dashboard()
    
    def update_dashboard(self):
        """Update all dashboard widgets"""
        summary = self.analyzer.get_summary()
        
        # Update summary widget
        total = sum(sum(d.values()) for d in summary.values())
        errors = sum(d.get("ERROR", 0) + d.get("CRITICAL", 0) + 
                    d.get("ALERT", 0) + d.get("EMERGENCY", 0) 
                    for d in summary.values())
        
        summary_text = f"""
Total Logs: {total}
Errors: {errors}
Error Rate: {(errors/total*100):.1f}% if total > 0 else 0
Domains: {len(summary)}
        """.strip()
        
        self.query_one("#summary-widget").update(summary_text)
        
        # Update priority widget
        priority_counts = defaultdict(int)
        for domain_data in summary.values():
            for priority, count in domain_data.items():
                priority_counts[priority] += count
        
        priority_text = "\n".join(
            f"{prio:12}: {count:4}"
            for prio, count in sorted(priority_counts.items())
        )
        self.query_one("#priority-widget").update(priority_text)
        
        # Update domains widget
        domain_text = "\n".join(
            f"{domain:12}: {sum(counts.values()):4}"
            for domain, counts in sorted(summary.items())
        )
        self.query_one("#domains-widget").update(domain_text)
        
        # Update errors widget (simplified)
        error_text = "Recent errors will appear here..."
        self.query_one("#errors-widget").update(error_text)

class LogViewerScreen(Screen):
    """Screen for viewing raw logs"""
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield DataTable(id="log-table")
        yield Footer()
    
    def on_mount(self) -> None:
        table = self.query_one("#log-table")
        table.add_columns("Time", "Process", "Priority", "Message")
        
        # Load and display some logs
        analyzer = LogAnalyzerTUI()
        if analyzer.load_logs(50):  # Small sample for table
            for line in analyzer.logs[:20]:
                try:
                    entry = json.loads(line)
                    process = entry.get("SYSLOG_IDENTIFIER", "unknown")
                    priority = analyzer.PRIO_MAP.get(
                        str(entry.get("PRIORITY", "6")), "INFO"
                    )
                    message = entry.get("MESSAGE", "")[:40] + "..."
                    
                    # Format time
                    ts = entry.get("__realtime_timestamp")
                    if ts:
                        dt = datetime.fromtimestamp(int(ts) / 1000000)
                        time_str = dt.strftime("%H:%M:%S")
                    else:
                        time_str = "??:??:??"
                    
                    table.add_row(time_str, process, priority, message)
                except json.JSONDecodeError:
                    continue

class LogalyzerTUI(App):
    """Main TUI application"""
    
    CSS = """
    Screen {
        background: $surface;
    }
    
    .widget-container {
        height: 100%;
        border: solid $secondary;
        margin: 1;
        padding: 1;
    }
    
    .widget-title {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }
    
    .widget {
        height: 100%;
        padding: 1;
    }
    
    DataTable {
        height: 1fr;
    }
    """
    
    BINDINGS = [
        ("d", "switch_mode('dashboard')", "Dashboard"),
        ("l", "switch_mode('logs')", "Log Viewer"),
        ("q", "quit", "Quit"),
    ]
    
    MODES = {
        "dashboard": DashboardScreen,
        "logs": LogViewerScreen,
    }
    
    def on_mount(self) -> None:
        """Start in dashboard mode"""
        self.switch_mode("dashboard")

def main():
    """Run the TUI"""
    app = LogalyzerTUI()
    app.run()

if __name__ == "__main__":
    main()