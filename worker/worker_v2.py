"""
JobBot Norway Worker v2
New architecture: Extract links first, then process each job individually
"""

import os
import sys
import time
import json
import logging
import requests
import re
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
import uuid

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

try:
    from supabase import create_client, Client
except ImportError:
    print("ERROR: supabase package not installed!")
    print("Install it: pip install supabase")
    sys.exit(1)

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("WARNING: Playwright not installed. Install with: pip install playwright && playwright install chromium")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('worker.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('JobBot-Worker-v2')


class JobBotWorkerV2:
    """Worker with new architecture: link extraction → individual processing"""

    def __init__(self):
        """Initialize worker with Supabase and Skyvern connections"""
        # Load environment variables
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
        self.skyvern_url = os.getenv('SKYVERN_API_URL', 'http://localhost:8000')

        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Missing SUPABASE_URL or SUPABASE_SERVICE_KEY environment variables")

        # Initialize Supabase client
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)

        # Worker ID
        self.worker_id = f"worker-v2-{uuid.uuid4().hex[:8]}"

        # Load Skyvern templates
        self.templates_dir = Path(__file__).parent / 'skyvern_templates'
        self.templates = self._load_templates()

        logger.info(f"🚀 Worker v2 initialized: {self.worker_id}")
        logger.info(f"📡 Supabase: {self.supabase_url}")
        logger.info(f"🤖 Skyvern: {self.skyvern_url}")

    def _load_templates(self) -> Dict[str, dict]:
        """Load Skyvern task templates"""
        templates = {}

        template_files = {
            'DETAIL': 'job_detail_template.json'
        }

        for key, filename in template_files.items():
            filepath = self.templates_dir / filename
            if filepath.exists():
                with open(filepath, 'r', encoding='utf-8') as f:
                    templates[key] = json.load(f)
                logger.info(f"✅ Loaded template: {key}")
            else:
                logger.warning(f"⚠️ Template not found: {filepath}")

        return templates

    def get_pending_tasks(self) -> List[Dict]:
        """Fetch pending scan tasks from Supabase"""
        try:
            response = self.supabase.table('scan_tasks').select('*').eq('status', 'PENDING').order('created_at').limit(5).execute()
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"❌ Error fetching tasks: {e}")
            return []

    def update_task_status(self, task_id: str, status: str, **kwargs):
        """Update scan task status"""
        try:
            update_data = {
                'status': status,
                'worker_id': self.worker_id,
                'updated_at': datetime.utcnow().isoformat()
            }

            if status == 'PROCESSING':
                update_data['started_at'] = datetime.utcnow().isoformat()
            elif status in ['COMPLETED', 'FAILED']:
                update_data['completed_at'] = datetime.utcnow().isoformat()

            # Add any additional fields
            update_data.update(kwargs)

            self.supabase.table('scan_tasks').update(update_data).eq('id', task_id).execute()
            logger.info(f"✅ Task {task_id[:8]}... updated to {status}")
        except Exception as e:
            logger.error(f"❌ Error updating task: {e}")

    def fetch_finn_search_html(self, url: str) -> Optional[str]:
        """Fetch HTML content from FINN.no search URL using Playwright

        FINN.no is a React/Next.js SPA - we need browser automation to render JavaScript
        """
        # Fallback to requests if Playwright not available (won't work for FINN.no)
        if not PLAYWRIGHT_AVAILABLE:
            logger.warning("⚠️ Playwright not available, using fallback (will likely fail for FINN.no)")
            return self._fetch_html_fallback(url)

        try:
            logger.info(f"🌐 Launching browser for: {url[:70]}...")

            with sync_playwright() as p:
                # Launch Chromium browser
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                )
                page = context.new_page()

                # Navigate to search page
                logger.info("📄 Loading page with JavaScript rendering...")
                page.goto(url, wait_until='networkidle', timeout=30000)

                # Wait for job listings to appear
                logger.info("⏳ Waiting for job listings...")
                try:
                    # Wait for job links to appear (new format: /job/ad/xxxxx or old format: finnkode=xxxxx)
                    page.wait_for_selector('a[href*="/job/"]', timeout=15000)
                    logger.info("✅ Job listings loaded!")
                except:
                    logger.warning("⚠️ No job listings found (page may be empty)")

                # Get rendered HTML
                html_content = page.content()

                browser.close()

                logger.info(f"✅ HTML fetched: {len(html_content)} characters")
                return html_content

        except Exception as e:
            logger.error(f"❌ Error fetching HTML with Playwright: {e}")
            return None

    def _fetch_html_fallback(self, url: str) -> Optional[str]:
        """Fallback method using requests (won't work for React SPAs like FINN.no)"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=30)

            if response.status_code == 200:
                return response.text
            else:
                logger.error(f"❌ HTTP {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            return None

    def extract_and_create_jobs(self, html_content: str, user_id: str, scan_task_id: str) -> List[Dict]:
        """Extract job links from HTML and create job entries in database"""
        try:
            logger.info("🔍 Extracting job links from HTML...")

            # DEBUG: Check for job links in HTML
            if '/job/ad/' in html_content:
                logger.info("✅ Found '/job/ad/' pattern in HTML")
            elif '/job/' in html_content:
                logger.info("⚠️ Found '/job/' but not '/job/ad/' in HTML")
            else:
                logger.warning("❌ No '/job/' pattern found in HTML at all!")

            # DEBUG: Sample
            sample = html_content[html_content.find('href='):html_content.find('href=')+200] if 'href=' in html_content else "No href found"
            logger.info(f"📄 Sample href: {sample}")

            # Call Supabase function to extract links and create jobs
            result = self.supabase.rpc(
                'create_jobs_from_finn_links',
                {
                    'p_user_id': user_id,
                    'p_scan_task_id': scan_task_id,
                    'p_html_content': html_content
                }
            ).execute()

            if result.data:
                logger.info(f"✅ Created/updated {len(result.data)} job entries")
                return result.data
            else:
                logger.warning("⚠️ No job links extracted from HTML")
                return []

        except Exception as e:
            logger.error(f"❌ Error extracting job links: {e}")
            return []

    def get_pending_jobs(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Get jobs pending Skyvern processing"""
        try:
            result = self.supabase.rpc(
                'get_pending_skyvern_jobs',
                {
                    'p_user_id': user_id,
                    'p_limit': limit
                }
            ).execute()

            return result.data if result.data else []
        except Exception as e:
            logger.error(f"❌ Error fetching pending jobs: {e}")
            return []

    def call_skyvern(self, template_key: str, url: str) -> Optional[Dict]:
        """Call Skyvern API to execute task"""
        if template_key not in self.templates:
            logger.error(f"❌ Template not found: {template_key}")
            return None

        # Get template and replace URL
        template = self.templates[template_key].copy()
        template['url'] = url

        try:
            logger.info(f"🤖 Calling Skyvern for: {url[:50]}...")

            # Create Skyvern task
            response = requests.post(
                f"{self.skyvern_url}/api/v1/tasks",
                json=template,
                timeout=300  # 5 minutes timeout
            )

            if response.status_code in [200, 201]:
                result = response.json()
                logger.info(f"✅ Skyvern task created: {result.get('task_id', 'N/A')}")

                # Wait for task completion (polling)
                task_id = result.get('task_id')
                if task_id:
                    return self._wait_for_skyvern_task(task_id)
                else:
                    return result
            else:
                logger.error(f"❌ Skyvern API error: {response.status_code} - {response.text}")
                return None

        except requests.exceptions.ConnectionError:
            logger.error(f"❌ Cannot connect to Skyvern at {self.skyvern_url}")
            logger.error("💡 Make sure Skyvern is running: docker-compose up skyvern")
            return None
        except Exception as e:
            logger.error(f"❌ Skyvern call failed: {e}")
            return None

    def _wait_for_skyvern_task(self, task_id: str, max_wait: int = 300) -> Optional[Dict]:
        """Poll Skyvern task status until completion"""
        start_time = time.time()

        while time.time() - start_time < max_wait:
            try:
                response = requests.get(f"{self.skyvern_url}/api/v1/tasks/{task_id}")

                if response.status_code == 200:
                    task_data = response.json()
                    status = task_data.get('status')

                    if status == 'completed':
                        logger.info(f"✅ Skyvern task completed: {task_id}")
                        return task_data
                    elif status == 'failed':
                        logger.error(f"❌ Skyvern task failed: {task_id}")
                        return task_data
                    else:
                        logger.info(f"⏳ Skyvern task {status}: {task_id}")
                        time.sleep(5)  # Wait 5 seconds before next check
                else:
                    logger.warning(f"⚠️ Task status check failed: {response.status_code}")
                    time.sleep(5)

            except Exception as e:
                logger.error(f"❌ Error checking task status: {e}")
                time.sleep(5)

        logger.error(f"❌ Skyvern task timeout: {task_id}")
        return None

    def update_job_with_details(self, job_id: str, skyvern_result: Dict):
        """Update job entry with details extracted by Skyvern"""
        try:
            extracted = skyvern_result.get('extracted_information', {})

            update_data = {
                'title': extracted.get('title') or extracted.get('job_title'),
                'company': extracted.get('company') or extracted.get('employer'),
                'description': extracted.get('description'),
                'location': extracted.get('location'),

                # Contact information
                'contact_name': extracted.get('contact_name'),
                'contact_email': extracted.get('contact_email'),
                'contact_phone': extracted.get('contact_phone'),

                # Address
                'address': extracted.get('address'),
                'city': extracted.get('city'),
                'postalCode': extracted.get('postalCode') or extracted.get('postal_code'),
                'county': extracted.get('county'),

                # Employment details
                'employment_type': extracted.get('employment_type'),
                'extent': extracted.get('extent'),
                'salary_range': extracted.get('salary_range'),
                'start_date': extracted.get('start_date'),
                'deadline': extracted.get('deadline'),

                # Arrays
                'requirements': extracted.get('requirements', []),
                'responsibilities': extracted.get('responsibilities', []),
                'benefits': extracted.get('benefits', []),

                # Application
                'application_url': extracted.get('application_url'),

                # Skyvern status
                'skyvern_status': 'COMPLETED' if skyvern_result.get('status') == 'completed' else 'FAILED',
                'task_id': skyvern_result.get('task_id'),
                'recording_url': skyvern_result.get('recording_url'),
                'processing_details': json.dumps(skyvern_result),

                # Mark as processed
                'is_processed': True,
                'updated_at': datetime.utcnow().isoformat()
            }

            # Remove None values
            update_data = {k: v for k, v in update_data.items() if v is not None}

            self.supabase.table('jobs').update(update_data).eq('id', job_id).execute()
            logger.info(f"✅ Updated job {job_id[:8]}... with Skyvern details")

        except Exception as e:
            logger.error(f"❌ Error updating job details: {e}")

    def process_task(self, task: Dict):
        """Process a single scan task with new architecture"""
        task_id = task['id']
        url = task['url']
        source = task['source']
        user_id = task['user_id']

        logger.info(f"\n{'='*60}")
        logger.info(f"📋 Processing task: {task_id[:8]}...")
        logger.info(f"🌐 Source: {source}")
        logger.info(f"🔗 URL: {url[:70]}...")
        logger.info(f"{'='*60}\n")

        # Update status to PROCESSING
        self.update_task_status(task_id, 'PROCESSING')

        try:
            # STEP 1: Fetch HTML from search page
            html_content = self.fetch_finn_search_html(url)

            if not html_content:
                raise Exception("Failed to fetch HTML from FINN.no")

            # STEP 2: Extract links and create job entries
            created_jobs = self.extract_and_create_jobs(html_content, user_id, task_id)

            if not created_jobs:
                logger.warning("⚠️ No jobs extracted from search results")
                self.update_task_status(
                    task_id,
                    'COMPLETED',
                    jobs_found=0,
                    jobs_saved=0
                )
                return

            logger.info(f"📊 Created {len(created_jobs)} job entries")

            # STEP 3: Process each job with Skyvern to get details
            jobs_processed = 0

            for i, job_entry in enumerate(created_jobs, 1):
                job_id = job_entry['job_id']
                job_url = job_entry['job_url']
                finnkode = job_entry['finnkode']

                logger.info(f"\n🔍 Processing job {i}/{len(created_jobs)}: finnkode={finnkode}")

                # Call Skyvern to extract detailed information
                skyvern_result = self.call_skyvern('DETAIL', job_url)

                if skyvern_result:
                    self.update_job_with_details(job_id, skyvern_result)
                    jobs_processed += 1
                    logger.info(f"✅ Job {i}/{len(created_jobs)} processed successfully")
                else:
                    logger.warning(f"⚠️ Job {i}/{len(created_jobs)} - Skyvern extraction failed")
                    # Mark as failed
                    self.supabase.table('jobs').update({
                        'skyvern_status': 'FAILED',
                        'updated_at': datetime.utcnow().isoformat()
                    }).eq('id', job_id).execute()

                # Small delay to avoid overwhelming Skyvern
                time.sleep(2)

            # STEP 4: Update task as completed
            self.update_task_status(
                task_id,
                'COMPLETED',
                jobs_found=len(created_jobs),
                jobs_saved=jobs_processed
            )

            logger.info(f"\n✅ Task completed: {jobs_processed}/{len(created_jobs)} jobs processed\n")

        except Exception as e:
            logger.error(f"❌ Task failed: {e}")

            # Update task as failed
            retry_count = task.get('retry_count', 0)
            max_retries = task.get('max_retries', 3)

            if retry_count < max_retries:
                # Retry later
                self.update_task_status(
                    task_id,
                    'PENDING',
                    error_message=str(e),
                    retry_count=retry_count + 1
                )
                logger.info(f"🔄 Task will be retried ({retry_count + 1}/{max_retries})")
            else:
                # Max retries reached
                self.update_task_status(
                    task_id,
                    'FAILED',
                    error_message=str(e),
                    retry_count=retry_count + 1
                )
                logger.error(f"❌ Task failed permanently after {max_retries} retries")

    def run(self, poll_interval: int = 10):
        """Main worker loop"""
        logger.info(f"\n{'='*60}")
        logger.info(f"🤖 JobBot Worker v2 Started")
        logger.info(f"🆔 Worker ID: {self.worker_id}")
        logger.info(f"⏱️ Poll Interval: {poll_interval}s")
        logger.info(f"📝 New Architecture: Link Extraction → Individual Processing")
        logger.info(f"{'='*60}\n")

        while True:
            try:
                # Fetch pending tasks
                tasks = self.get_pending_tasks()

                if tasks:
                    logger.info(f"📥 Found {len(tasks)} pending task(s)")

                    for task in tasks:
                        self.process_task(task)
                else:
                    logger.info(f"💤 No pending tasks. Waiting {poll_interval}s...")

                # Wait before next check
                time.sleep(poll_interval)

            except KeyboardInterrupt:
                logger.info("\n⛔ Worker stopped by user")
                break
            except Exception as e:
                logger.error(f"❌ Worker error: {e}")
                time.sleep(poll_interval)


if __name__ == '__main__':
    try:
        worker = JobBotWorkerV2()
        worker.run(poll_interval=10)
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)
