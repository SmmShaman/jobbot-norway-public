"""Entry point executed by n8n via:
     docker exec jobbot python -m src.apply <job_id>
"""
import sys
import os
import json
import asyncio
from pathlib import Path
from typing import Optional

from .utils.db import get_job, update_status
from playwright.async_api import async_playwright, Page

# --- Config ---
DATA_DIR = Path("/app/data")
LETTERS_DIR = DATA_DIR / "letters"
RESUME_PDF = DATA_DIR / "attachments" / "resume.pdf"
ADAPTERS_DIR = Path("src/utils/adapters")

async def submit_application(job_url: str, letter_text: str, fn_number: str) -> None:
    """Handles the full application flow, including redirects."""
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
        page = await browser.new_page()
        await page.goto(job_url, wait_until="load")

        # --- NEW LOGIC: Handle potential cookie banner ---
        cookie_accept_selector = "button#onetrust-accept-btn-handler"
        try:
            print("Checking for cookie banner...")
            await page.locator(cookie_accept_selector).click(timeout=5000)
            print("Cookie banner accepted.")
            await page.wait_for_timeout(1000) #
        except Exception:
            print("Cookie banner not found or already accepted.")
        # --- END OF NEW LOGIC ---

        if 'finn.no' in page.url:
            print("On finn.no, attempting to redirect to actual application page...")
            finn_adapter_file = ADAPTERS_DIR / "finn.json"
            if not finn_adapter_file.exists(): raise RuntimeError("finn.json adapter is missing!")
            
            finn_rules = json.loads(finn_adapter_file.read_text(encoding="utf-8"))
            
            print("Clicking redirect button and waiting for navigation...")
            await page.locator(finn_rules["redirect_button"]).click()
            await page.wait_for_load_state("domcontentloaded", timeout=60000)
            print(f"Successfully redirected to new URL: {page.url}")

        current_domain = page.url.split("/")[2].replace("www.", "")
        adapter_file = ADAPTERS_DIR / f"{current_domain.split('.')[0]}.json"
        if not adapter_file.exists():
            raise RuntimeError(f"No adapter found for domain: {current_domain}")

        rules = json.loads(adapter_file.read_text(encoding="utf-8"))
        print(f"Using adapter for {current_domain} to fill the form.")

        if rules.get("name"):
            await page.fill(rules["name"], os.getenv("FULL_NAME", "Default Name"))
        if rules.get("email"):
            await page.fill(rules["email"], os.getenv("EMAIL_ADDRESS", "default@email.com"))
        if rules.get("phone"):
            await page.fill(rules["phone"], os.getenv("PHONE_NUMBER", "12345678"))

        await page.fill(rules["cover"], letter_text[:4000])
        await page.set_input_files(rules["cv"], str(RESUME_PDF))
        
        print("Form filled, attempting to submit...")
        # await page.click(rules["send"], timeout=30_000) 
        print("Submission step is currently commented out for safety.")

        await browser.close()

async def main(job_id: int) -> None:
    job = get_job(job_id)
    if not job: raise RuntimeError(f"job_id {job_id} not found in DB")

    letter_path = LETTERS_DIR / f"{job_id}.txt"
    if not letter_path.exists(): raise RuntimeError(f"Letter file {letter_path} missing")
    
    letter_text = letter_path.read_text(encoding="utf-8")
    fn_number = os.getenv("FN_NUMBER")
    
    try:
        await submit_application(job["url"], letter_text, fn_number)
        update_status(job_id, "APPLIED_DIRECT (simulated)")
        print(f"[OK] Applied for job {job_id}")
    except Exception as e:
        print(f"[ERROR] job {job_id}: {e}", file=sys.stderr)
        update_status(job_id, "ERROR_PLAYWRIGHT")
        raise

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m src.apply <job_id>", file=sys.stderr)
        sys.exit(1)
    asyncio.run(main(int(sys.argv[1])))
