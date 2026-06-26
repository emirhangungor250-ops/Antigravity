"""
Toplu outreach gonderici (SABLON)
=================================
CSV listesinden okuyup her satira kisisellestirilmis mail gonderir,
durumu CSV'ye geri yazar. Orijinalde skill sahibinin gercek kampanya
verisi (CSV yolu, marka, gonderen kimligi) vardi; jenerik sablona indirildi.

Kullanmadan once: CSV_PATH / TEMPLATE_PATH yollarini, gonderen kimligini
ve TEMPLATE_BODY metnini kendi kampanyaniza gore degistirin.
"""

import csv
import subprocess
import time
import os
import sys

# TODO: Kendi yollarinizla degistirin (relative yol onerilir).
CSV_PATH = "data/outreach_tracking.csv"
SCRIPT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TEMPLATE_PATH = "data/outreach_template.md"

if not os.path.exists(TEMPLATE_PATH):
    print(f"ERROR: Template not found at {TEMPLATE_PATH}")
    sys.exit(1)

# TODO: Kendi marka/kampanya metninizle degistirin.
TEMPLATE_SUBJECT = "Collaboration Inquiry - <MARKA_ADI>"
TEMPLATE_BODY = """Hi {Name},

Hope you are doing well!

I'm <GONDEREN_ADI> from the team at <MARKA_ADI>. I've been following your profile and love the content you post.

We would love to collaborate with you on a short promotional video.

Could you please let me know your standard rate for a dedicated video integration?

Best regards,
<GONDEREN_ADI>
<MARKA_ADI>"""

HTML_BODY = TEMPLATE_BODY.replace("\n\n", "</p><p>").replace("\n", "<br>")
HTML_BODY = f"<p>{HTML_BODY}</p>"

print("Starting mass outreach using the template...")

rows = []
with open(CSV_PATH, "r", encoding="utf-8") as f:
    reader = csv.reader(f)
    for row in reader:
        rows.append(row)

sent_count = 0
failed_count = 0

for i in range(2, len(rows)):
    row = rows[i]
    name = row[0]
    email = row[2]
    status = row[8] if len(row) > 8 else ""

    # Skip if already Sent or Failed
    if status.strip() != "":
        continue

    personalized_html = HTML_BODY.replace("{Name}", name)

    cmd = [
        "python3",
        "_skills/eposta-gonderim/scripts/send_email.py",
        "--to", email,
        "--subject", TEMPLATE_SUBJECT,
        "--body", personalized_html,
        "--csv", CSV_PATH,
        "--row_id", str(i - 1)
    ]

    print(f"[{sent_count+failed_count+1}] Sending to {name} ({email}) ...")
    res = subprocess.run(cmd, cwd=SCRIPT_DIR, capture_output=True, text=True)

    if res.returncode == 0 and "Success" in res.stdout:
        print(f"  SUCCESS")
        sent_count += 1
    elif res.returncode == 0 and "Failed" in res.stdout:
        print(f"  FAILED (But script finished)")
        print(f"  Output: {res.stdout.strip()}")
        failed_count += 1
    else:
        print(f"  CRITICAL ERROR (Script crashed)")
        print(f"  Output: {res.stdout.strip()}")
        print(f"  Stderr: {res.stderr.strip()}")
        failed_count += 1

    time.sleep(2)

print(f"\n--- OUTREACH COMPLETE ---")
print(f"Total Sent: {sent_count}")
print(f"Total Failed: {failed_count}")
