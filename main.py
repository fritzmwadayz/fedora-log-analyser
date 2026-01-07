import subprocess, json
from collections import defaultdict
import datetime

# NOTE:
# This parser assumes classic syslog-style text output.
# It WILL break on format changes, journald JSON is preferred.
# This exists for exploration, not correctness.

output = subprocess.run(
    ["journalctl", "--output=json", "--no-pager"],
    capture_output=True,
    text=True
)

# Priority labels for readability
PRIO_MAP = {
    "0": "EMERGENCY", "1": "ALERT", "2": "CRITICAL", "3": "ERROR",
    "4": "WARNING", "5": "NOTICE", "6": "INFO", "7": "DEBUG"
}

lines = output.stdout.splitlines()

month_counts = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))

processes = set()

domain_processes = defaultdict(set)

DOMAIN_MAP = {
    "KERNEL": {
        "kernel",
    },
    "BOOT": {
        "systemd", "dracut", "dracut-cmdline",
        "systemd-modules-load", "systemd-fsck",
    },
    "NETWORK": {
        "NetworkManager", "wpa_supplicant",
        "ModemManager", "avahi-daemon", "chronyd",
    },
    "AUDIO": {
        "pipewire", "wireplumber", "alsactl",
    },
    "SECURITY": {
        "auditd", "audit", "polkitd",
        "setroubleshoot", "sudo",
    },
    "PACKAGE_MGMT": {
        "dnf", "dnf5", "dnf5daemon-server",
        "PackageKit", "fwupd",
    },
    "CRASH_HANDLING": {
        "abrt-server", "abrtd",
        "abrt-dump-journal-core",
        "systemd-coredump",
    },
    "SCHEDULERS": {
        "crond", "CROND", "atd", "anacron",
    },
    "DESKTOP": {
        "xfce4-terminal", "dolphin",
        "vlc", "chrome", "brave-browser-stable",
    },
}


def classify_process(proc):
    if not proc or proc == "unknown":
        return "MISC"
        
    for domain, names in DOMAIN_MAP.items():
        if proc in names:
            return domain

    if proc.startswith("systemd"):
        return "BOOT"

    return "MISC"

print("Some bad stuff could happen")

# Counter to track progress
line_count = 0
processed_count = 0

for line in lines:
    line_count += 1
    if line_count % 10000 == 0:
        print(f"Processing line {line_count}...")
        
    try:
        # Parse the JSON object for each log line
        log_entry = json.loads(line)
        
        # Extract log fields
        process = log_entry.get("SYSLOG_IDENTIFIER", "unknown")
        if not process and "_COMM" in log_entry:
            process = log_entry.get("_COMM", "unknown")
            
        priority_num = str(log_entry.get("PRIORITY", "6"))  # Default to Info
        priority = PRIO_MAP.get(priority_num, "INFO")

        # Get Month from the timestamp
        timestamp = log_entry.get("__realtime_timestamp")
        if timestamp:
            # Convert microseconds to seconds
            dt = datetime.datetime.fromtimestamp(int(timestamp) / 1000000)
            month = dt.strftime("%b")
        else:
            # Fallback to _SOURCE_REALTIME_TIMESTAMP or current month
            alt_timestamp = log_entry.get("_SOURCE_REALTIME_TIMESTAMP")
            if alt_timestamp:
                dt = datetime.datetime.fromtimestamp(int(alt_timestamp) / 1000000)
                month = dt.strftime("%b")
            else:
                month = datetime.datetime.now().strftime("%b")

        # Classification logic
        domain = classify_process(process)

        # Increment count for that specific priority
        month_counts[month][domain][priority] += 1
        processed_count += 1

    except (json.JSONDecodeError, KeyError, ValueError) as e:
        continue

print(f"\nProcessed {processed_count} out of {line_count} total lines")

# Print output
if not month_counts:
    print("\nNo data processed!")
else:
    for month in sorted(month_counts.keys()):
        print(f"\n{month}")
        for domain in sorted(month_counts[month].keys()):
            print(f"  {domain}:")
            # Sort priorities by severity (Emergency first, Debug last)
            priority_order = ["EMERGENCY", "ALERT", "CRITICAL", "ERROR", 
                            "WARNING", "NOTICE", "INFO", "DEBUG"]
            
            for prio in priority_order:
                count = month_counts[month][domain].get(prio, 0)
                if count > 0:
                    print(f"    - {prio}: {count}")