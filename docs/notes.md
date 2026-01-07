# Notes – Log Analyzer

## Day 1 – Getting Started.
First I used the python subprocess module to execute the journalctl command.
Didn't know the output needed to be stored first to prevent spamming the terminal with the command output but came to that realization and prompty dealt with that.

The logs are stored as single large string. To access individual logs python string operations come in handy. By simply splitting the bigger string by \n (newline) entries we can access the individual logs. This is of course only true if there are no multiline entries. However in that case we set a condition to ignore lines failing to meet certain criteria e.g minimum length, invalid first 3 characters etcetra.

This of course means that in case of logs with a different structure unlike that of journalctl, or if journalctl log format changes this script will not work as expected.

Anyway now that I had the logs the next problem was sorting them.

```py
import subprocesss

output = subprocess.run(
    ["journalctl", "--no-pager"],
    capture_output=True,
    text=True
)

logs = output.stdout
```

## Day 2 - Working on the logs:
The logs have a couple of characteristics that could be of interest. These include month, process and priority.

I decided to start with sorting by month first since it was the most straight forward thing. The month is usually the first detail of the logs. So the script would extract the month from the log and for each entry that month is mentioned it would increment a counter. When this part was complete a simple table showing month and message count would be printed.

```py
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
```

## Day 3 - Still working on the logs:
Sorting by month has been successfull but is unfortunately not helpful for any proper or at least somewhat good log analysis. To improve on that I needed to now sort by process. I would go about that using python string operations as I had done before.

```py
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
```

However there are too many processes and I would need to streamline this leading to the creation of process classifications.

# Day 4 - Upgraded the script to use json
The previous method to extract and store logs had a major downside. It's a human readable version and lacks a some fields that are necessary for the new form of sort i.e by priority, that I wanted to implement. This operation does however use a lot of memory while executing. Otherwise not too many observations made yet. On to the next.

```py
# Updated journalctl call
output = subprocess.run(
    ["journalctl", "--output=json", "--no-pager"],
    capture_output=True,
    text=True
)
```

# Day 5 - Build First Working REPL