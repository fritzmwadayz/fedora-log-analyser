import json
import csv
from datetime import datetime
from collections import defaultdict

def export_data(self, format: str):
    """Export data in specified format"""
    if not self.processed_data:
        print("No data to export")
        return
    
    format = format.lower()
    
    if format == "json":
        self._export_json()
    elif format == "csv":
        self._export_csv()
    elif format == "html":
        self._export_html()
    elif format == "markdown":
        self._export_markdown()
    else:
        print("Unknown export format. Use: json, csv, html, markdown")

def _export_json(self):
    """Export to JSON format"""
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