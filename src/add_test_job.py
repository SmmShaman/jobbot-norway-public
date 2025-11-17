from .utils.db import _conn

TEST_JOB_ID = 123
TEST_JOB_URL = "https://www.finn.no/job/fulltime/ad.html/2025/7/7/123/456789"
TEST_JOB_TITLE = "Test Job From Script"

print(f"Attempting to insert test job with ID: {TEST_JOB_ID}")

try:
    with _conn() as cx:
        # Спочатку видаляємо, щоб скрипт можна було запускати багато разів
        cx.execute("DELETE FROM jobs WHERE id = ?", (TEST_JOB_ID,))
        
        # Вставляємо новий тестовий запис
        cx.execute(
            "INSERT INTO jobs (id, url, title, status) VALUES (?, ?, ?, ?)",
            (TEST_JOB_ID, TEST_JOB_URL, TEST_JOB_TITLE, 'NEW'),
        )
        cx.commit()
    print(f"Successfully inserted job_id {TEST_JOB_ID}.")
except Exception as e:
    print(f"An error occurred: {e}")
