"""
JobBot Norway Worker
Runs on local PC, processes scan tasks from Supabase queue using Skyvern
"""

import os
import sys
import time
import json
import logging
import requests
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
import uuid

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from supabase import create_client, Client
except ImportError:
    print("ERROR: supabase package not installed!")
    print("Install it: pip install supabase")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('worker.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('JobBot-Worker')


class JobBotWorker:
    """Worker that processes scan tasks using Skyvern"""

    def __init__(self):
        """Initialize worker with Supabase and Skyvern connections"""
        # Load environment variables
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
        self.skyvern_url = os.getenv('SKYVERN_API_URL', 'http://localhost:8000')
        self.skyvern_api_key = os.getenv('SKYVERN_API_KEY', '')

        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Missing SUPABASE_URL or SUPABASE_SERVICE_KEY environment variables")

        # Initialize Supabase client
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)

        # Worker ID
        self.worker_id = f"worker-{uuid.uuid4().hex[:8]}"

        # Load Skyvern templates
        self.templates_dir = Path(__file__).parent / 'skyvern_templates'
        self.templates = self._load_templates()

        logger.info(f"🚀 Worker initialized: {self.worker_id}")
        logger.info(f"📡 Supabase: {self.supabase_url}")
        logger.info(f"🤖 Skyvern: {self.skyvern_url}")
        if self.skyvern_api_key:
            logger.info(f"🔑 Skyvern API Key: {'*' * 20}{self.skyvern_api_key[-8:]}")

    def _load_templates(self) -> Dict[str, dict]:
        """Load Skyvern task templates"""
        templates = {}

        template_files = {
            'FINN': 'finn_no_template.json',
            'NAV': 'nav_no_template.json',
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

            # Filter out tasks that have reached max retries (stuck tasks)
            tasks = response.data if response.data else []
            valid_tasks = []

            for task in tasks:
                retry_count = task.get('retry_count', 0)
                max_retries = task.get('max_retries', 3)

                if retry_count >= max_retries:
                    # Mark stuck task as FAILED
                    logger.warning(f"⚠️ Task {task['id'][:8]}... stuck in PENDING with {retry_count}/{max_retries} retries - marking as FAILED")
                    self.update_task_status(task['id'], 'FAILED', error_message=task.get('error_message', 'Max retries reached'))
                else:
                    valid_tasks.append(task)

            return valid_tasks
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

    def call_skyvern(self, template_key: str, url: str) -> Optional[Dict]:
        """Call Skyvern API to execute task"""
        if template_key not in self.templates:
            logger.error(f"❌ Template not found: {template_key}")
            return None

        # Get template and replace URL
        template = self.templates[template_key].copy()
        template['url'] = url

        try:
            logger.info(f"🤖 Calling Skyvern API: {self.skyvern_url}")
            logger.info(f"📄 Template: {template_key}, URL: {url[:50]}...")

            # Prepare headers with API key if available
            headers = {}
            if self.skyvern_api_key:
                headers['x-api-key'] = self.skyvern_api_key

            # Create Skyvern task
            response = requests.post(
                f"{self.skyvern_url}/api/v1/tasks",
                json=template,
                headers=headers,
                timeout=300  # 5 minutes timeout
            )

            if response.status_code == 200 or response.status_code == 201:
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

        # Prepare headers with API key if available
        headers = {}
        if self.skyvern_api_key:
            headers['x-api-key'] = self.skyvern_api_key

        while time.time() - start_time < max_wait:
            try:
                response = requests.get(
                    f"{self.skyvern_url}/api/v1/tasks/{task_id}",
                    headers=headers
                )

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

    def save_job_urls_immediately(self, jobs: List[Dict], task_id: str, user_id: str, source: str) -> int:
        """STAGE 1: Save job URLs immediately with minimal data so they appear in Dashboard right away"""
        saved_count = 0

        for job in jobs:
            try:
                # Skip if no URL (required for duplicate detection)
                if not job.get('url'):
                    logger.warning(f"⚠️ Skipping job without URL: {job.get('title', 'N/A')}")
                    continue

                # Prepare minimal job data (just URL + basic info)
                job_data = {
                    # Required fields
                    'user_id': user_id,
                    'scan_task_id': task_id,
                    'source': source,
                    'title': job.get('title', 'Unknown Title'),
                    'company': job.get('company', 'Unknown Company'),
                    'url': job.get('url'),

                    # Basic info from listing page
                    'location': job.get('location'),
                    'description': job.get('description'),  # Short description from listing
                    'posted_date': job.get('posted_date'),
                    'finnkode': job.get('finnkode') if source == 'FINN' else None,

                    # Metadata
                    'scraped_at': datetime.utcnow().isoformat(),
                    'status': 'NEW',
                    'is_processed': False,
                    'skyvern_status': 'URL_EXTRACTED',  # Mark that we only have URL so far

                    # Empty arrays for now (will be filled in stage 2)
                    'requirements': [],
                    'responsibilities': [],
                    'benefits': []
                }

                # Insert or update if exists
                result = self.supabase.table('jobs').upsert(
                    job_data,
                    on_conflict='user_id,url'
                ).execute()

                if result.data:
                    saved_count += 1
                    logger.info(f"✅ Saved URL: {job_data['title'][:40]} | {job_data['company'][:25]} | {job_data['url'][:50]}...")

            except Exception as e:
                error_msg = str(e).lower()
                if 'duplicate' in error_msg or 'unique constraint' in error_msg:
                    logger.info(f"⏭️ Job URL already exists: {job.get('url', 'N/A')[:60]}...")
                else:
                    logger.error(f"❌ Error saving job URL '{job.get('title', 'N/A')[:40]}': {e}")

        logger.info(f"📊 Stage 1 complete: {saved_count} job URLs saved to database (visible in Dashboard now!)")
        return saved_count

    def update_job_details(self, job_url: str, details: Dict, user_id: str) -> bool:
        """STAGE 2: Update job with detailed information from job detail page"""
        try:
            # Prepare update data with all details
            update_data = {
                # Full description (from detail page, not listing summary)
                'description': details.get('description'),

                # Contact information
                'contact_name': details.get('contact_name'),
                'contact_email': details.get('contact_email'),
                'contact_phone': details.get('contact_phone'),

                # Address details
                'address': details.get('address'),
                'city': details.get('city'),
                'postalCode': details.get('postalCode') or details.get('postal_code'),
                'county': details.get('county'),
                'country': details.get('country', 'Norge'),

                # Employment details
                'employment_type': details.get('employment_type'),
                'extent': details.get('extent'),
                'salary_range': details.get('salary_range'),
                'start_date': details.get('start_date'),
                'deadline': details.get('deadline'),

                # Arrays
                'requirements': details.get('requirements', []) if isinstance(details.get('requirements'), list) else [],
                'responsibilities': details.get('responsibilities', []) if isinstance(details.get('responsibilities'), list) else [],
                'benefits': details.get('benefits', []) if isinstance(details.get('benefits'), list) else [],

                # Additional fields
                'work_arrangement': details.get('work_arrangement'),
                'application_url': details.get('application_url'),

                # Update status
                'skyvern_status': 'DETAILS_EXTRACTED',
                'updated_at': datetime.utcnow().isoformat()
            }

            # Update existing job by URL
            result = self.supabase.table('jobs').update(update_data).eq('url', job_url).eq('user_id', user_id).execute()

            if result.data:
                logger.info(f"✅ Updated details for: {job_url[:60]}...")
                return True
            else:
                logger.warning(f"⚠️ No job found to update for URL: {job_url[:60]}...")
                return False

        except Exception as e:
            logger.error(f"❌ Error updating job details for {job_url[:60]}: {e}")
            return False

    def process_task(self, task: Dict):
        """Process a single scan task with 2-stage approach"""
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
            # ========== STAGE 1: Extract job URLs from listing page ==========
            logger.info("🔍 STAGE 1: Extracting job URLs from listing page...")
            template_key = source  # 'FINN' or 'NAV'
            result = self.call_skyvern(template_key, url)

            if not result:
                raise Exception("Skyvern returned no results")

            # Extract jobs from result
            extracted_data = result.get('extracted_information', {})
            jobs_list = extracted_data.get('jobs', [])

            if not jobs_list:
                logger.warning("⚠️ No jobs found in Skyvern result")
                self.update_task_status(
                    task_id,
                    'COMPLETED',
                    jobs_found=0,
                    jobs_saved=0
                )
                return

            logger.info(f"✅ Found {len(jobs_list)} job URLs")

            # IMMEDIATELY save URLs to database (user will see them in Dashboard!)
            saved_urls_count = self.save_job_urls_immediately(jobs_list, task_id, user_id, source)

            # Update task with URLs saved
            self.update_task_status(
                task_id,
                'PROCESSING',
                jobs_found=len(jobs_list),
                jobs_saved=saved_urls_count
            )

            logger.info(f"✅ Stage 1 complete: {saved_urls_count} jobs visible in Dashboard!")

            # ========== STAGE 2: Extract detailed info for each job ==========
            logger.info(f"\n🔍 STAGE 2: Extracting details for {len(jobs_list)} jobs...")

            details_success_count = 0
            for i, job in enumerate(jobs_list, 1):
                job_url = job.get('url')
                if not job_url:
                    logger.warning(f"⚠️ Job {i}/{len(jobs_list)} has no URL, skipping detail extraction")
                    continue

                logger.info(f"\n📄 [{i}/{len(jobs_list)}] Getting details: {job.get('title', 'N/A')[:45]}...")
                logger.info(f"    URL: {job_url[:70]}...")

                # Call Skyvern to get job details
                detail_result = self.call_skyvern('DETAIL', job_url)

                if detail_result and detail_result.get('extracted_information'):
                    # Update database with detailed information
                    details = detail_result['extracted_information']
                    success = self.update_job_details(job_url, details, user_id)

                    if success:
                        details_success_count += 1
                        logger.info(f"✅ [{i}/{len(jobs_list)}] Details saved! (Contact: {details.get('contact_name', 'N/A')}, Email: {details.get('contact_email', 'N/A')})")
                    else:
                        logger.warning(f"⚠️ [{i}/{len(jobs_list)}] Failed to update database with details")
                else:
                    logger.warning(f"⚠️ [{i}/{len(jobs_list)}] Skyvern didn't extract details, job will have URL only")

                # Small delay to avoid overwhelming Skyvern
                time.sleep(2)

            logger.info(f"\n✅ Stage 2 complete: {details_success_count}/{len(jobs_list)} jobs have full details")

            # Update task as completed
            self.update_task_status(
                task_id,
                'COMPLETED',
                jobs_found=len(jobs_list),
                jobs_saved=saved_urls_count  # URLs saved, details are extra
            )

            logger.info(f"\n{'='*60}")
            logger.info(f"✅ Task completed successfully!")
            logger.info(f"📊 Summary:")
            logger.info(f"   - URLs found: {len(jobs_list)}")
            logger.info(f"   - URLs saved: {saved_urls_count}")
            logger.info(f"   - Details extracted: {details_success_count}")
            logger.info(f"{'='*60}\n")

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
        logger.info(f"🤖 JobBot Worker Started")
        logger.info(f"🆔 Worker ID: {self.worker_id}")
        logger.info(f"⏱️ Poll Interval: {poll_interval}s")
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
        worker = JobBotWorker()
        worker.run(poll_interval=10)
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)
