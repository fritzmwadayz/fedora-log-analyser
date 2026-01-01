import subprocess

#output = f"{subprocess.run('journalctl')}"

output = subprocess.run(
    ["journalctl", "--no-pager"],
    capture_output=True,
    text=True
)

logs = output.stdout

lines = logs.split("\n")

counts = {}

fake_logs = """Dec 30 16:02:14 host systemd[1]: Started something
Dec 30 16:05:22 host sshd[944]: Accepted password
Jan 02 09:11:01 host NetworkManager[812]: State changed
Jan 02 09:15:44 host systemd[1]: Stopped something
Jan 03 10:00:00 host sshd[944]: Failed password
"""

#lines = fake_logs.split("\n")
 
month_counts = {}

for line in lines:
    if len(line) < 3:
        continue

    VALID_MONTHS = {"Jan","Feb","Mar","Apr","May","Jun",
                    "Jul","Aug","Sep","Oct","Nov","Dec"}

    month = line[:3]

    if month not in VALID_MONTHS:
        continue
    #month = line[:3]

    if month in month_counts:
        month_counts[month] += 1
    else:
        month_counts[month] = 1

print("Month  Count")
print("-------------")

for month, count in month_counts.items():
    print(f"{month}    {count}")