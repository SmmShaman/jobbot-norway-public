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

            # Create Skyvern task
            response = requests.post(
                f"{self.skyvern_url}/api/v1/tasks",
                json=template,
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

    def save_jobs_to_database(self, jobs: List[Dict], task_id: str, user_id: str, source: str):
        """Save extracted jobs to Supabase"""
        saved_count = 0

        for job in jobs:
            try:
                # Prepare job data
                job_data = {
                    'user_id': user_id,
                    'scan_task_id': task_id,
                    'source': source,
                    'title': job.get('title', 'Unknown Title'),
                    'company': job.get('company', 'Unknown Company'),
                    'location': job.get('location'),
                    'url': job.get('url'),
                    'description': job.get('description'),
                    'contact_email': job.get('contact_email'),
                    'contact_phone': job.get('contact_phone'),
                    'deadline': job.get('deadline'),
                    'salary_range': job.get('salary_range'),
                    'employment_type': job.get('employment_type'),
                    'requirements': job.get('requirements'),
                    'benefits': job.get('benefits'),
                    'status': 'NEW',
                    'relevance_score': 0,
                    'discovered_at': datetime.utcnow().isoformat()
                }

                # Insert job (ignore duplicates by URL)
                self.supabase.table('jobs').insert(job_data).execute()
                saved_count += 1
                logger.info(f"💾 Saved job: {job_data['title']} at {job_data['company']}")

            except Exception as e:
                # Likely duplicate (URL already exists)
                if 'duplicate key value' in str(e).lower():
                    logger.info(f"⏭️ Job already exists: {job.get('url', 'N/A')[:50]}...")
                else:
                    logger.error(f"❌ Error saving job: {e}")

        return saved_count

    def process_task(self, task: Dict):
        """Process a single scan task"""
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
            # Step 1: Get list of jobs from search page
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

            logger.info(f"📊 Found {len(jobs_list)} jobs")

            # Step 2: For each job, get detailed information
            detailed_jobs = []
            for i, job in enumerate(jobs_list, 1):
                job_url = job.get('url')
                if not job_url:
                    logger.warning(f"⚠️ Job {i} has no URL, skipping detail extraction")
                    detailed_jobs.append(job)
                    continue

                logger.info(f"🔍 Extracting details for job {i}/{len(jobs_list)}: {job.get('title', 'N/A')[:40]}...")

                detail_result = self.call_skyvern('DETAIL', job_url)

                if detail_result and detail_result.get('extracted_information'):
                    # Merge list data with detailed data
                    detailed_job = {**job, **detail_result['extracted_information']}
                    detailed_jobs.append(detailed_job)
                    logger.info(f"✅ Got detailed data for: {detailed_job.get('title', 'N/A')[:40]}")
                else:
                    # Use basic data if detail extraction failed
                    logger.warning(f"⚠️ Detail extraction failed, using basic data")
                    detailed_jobs.append(job)

                # Small delay to avoid overwhelming Skyvern
                time.sleep(2)

            # Step 3: Save all jobs to database
            saved_count = self.save_jobs_to_database(detailed_jobs, task_id, user_id, source)

            # Update task as completed
            self.update_task_status(
                task_id,
                'COMPLETED',
                jobs_found=len(jobs_list),
                jobs_saved=saved_count
            )

            logger.info(f"\n✅ Task completed: {saved_count}/{len(jobs_list)} jobs saved\n")

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
