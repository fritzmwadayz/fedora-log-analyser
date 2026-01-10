import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from datetime import datetime
import json
from collections import defaultdict

def show_visualization(self):
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