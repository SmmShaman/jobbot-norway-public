import sys
from .utils.db import _conn

if len(sys.argv) < 2:
    print("Error: Please provide a URL as an argument.")
    sys.exit(1)

TEST_JOB_ID = 123
NEW_URL = sys.argv[1]

print(f"Updating URL for job_id {TEST_JOB_ID} to: {NEW_URL}")

try:
    with _conn() as cx:
        cx.execute("UPDATE jobs SET url = ? WHERE id = ?", (NEW_URL, TEST_JOB_ID))
        cx.commit()
    print("Successfully updated.")
except Exception as e:
    print(f"An error occurred: {e}")
