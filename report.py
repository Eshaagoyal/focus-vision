import os
from datetime import datetime


def save_report(avg, distractions, mins, secs, log_file):
    """
    Saves a human-readable session report as a .txt file
    in the logs folder.
    """
    os.makedirs("logs", exist_ok=True)
    timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename   = f"logs/report_{timestamp}.txt"
    date_str   = datetime.now().strftime("%d %B %Y, %I:%M %p")

    if avg >= 75:
        grade = "Excellent 🟢"
    elif avg >= 55:
        grade = "Good 🟡"
    elif avg >= 35:
        grade = "Needs Improvement 🟠"
    else:
        grade = "Poor 🔴"

    report = f"""
====================================
     ATTENTION TRACKER REPORT
====================================
Date         : {date_str}
Duration     : {mins}m {secs}s
------------------------------------
Avg Score    : {avg}/100
Grade        : {grade}
Distractions : {distractions} events
------------------------------------
CSV Log      : {log_file}
====================================
Tips:
- Score 70+  → You were focused
- Score 40+  → Mildly distracted
- Score <40  → Significantly off task

Improve by:
  * Reducing phone usage during study
  * Taking breaks every 25 minutes
  * Ensuring good lighting on face
====================================
"""

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(report)

    print(report)
    print(f"Report saved to: {filename}")
    return filename