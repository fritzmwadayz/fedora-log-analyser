from collections import defaultdict
from datetime import datetime

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

# Note: _demo_export_formats moved to data/export.py
# Note: _demo_batch_processing and _demo_integration_hooks are omitted for brevity
# as they are mostly demo stubs