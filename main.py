import subprocess

# NOTE:
# This parser assumes classic syslog-style text output.
# It WILL break on format changes, journald JSON is preferred.
# This exists for exploration, not correctness.

output = subprocess.run(
    ["journalctl", "--no-pager"],
    capture_output=True,
    text=True
)

logs = output.stdout

lines = logs.split("\n")

counts = {}
 
month_counts = {}

VALID_MONTHS = {"Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"}

for line in lines:
    if len(line) < 3:
        continue

    month = line[:3]

    if month not in VALID_MONTHS:
        continue

    if month in month_counts:
        month_counts[month] += 1
    else:
        month_counts[month] = 1

print("Month  Count")
print("-------------")

for month, count in month_counts.items():
    print(f"{month}    {count}")

print("Some bad stuff could happen")

processes = set()

for line in lines:
    if len(line) < 3:
        continue

    parts = line.split()
    if len(parts) < 5:
        continue

    month = parts[0]
    if month not in VALID_MONTHS:
        continue

    # process is usually field 4: process[pid]:
    if "[" not in parts[4]:
        continue

    process = parts[4].split("[", 1)[0]
    processes.add(process)

for process in sorted(processes):
    print(process)
