// JobBot Norway - TypeScript Type Definitions

export interface User {
  id: string;
  username: string;
  full_name?: string;
  email: string;
  phone?: string;
  fnr?: string;
  avatar_url?: string;
  created_at: string;
  updated_at: string;
}

export interface UserSettings {
  id: string;
  user_id: string;
  nav_search_urls: string[];
  finn_search_urls: string[];
  keywords: string[];
  exclude_keywords: string[];
  preferred_locations: string[];
  resume_storage_path?: string;
  unified_profile?: UnifiedProfile;
  skills: string[];
  experience_years: number;
  min_relevance_score: number;
  auto_apply_threshold: number;
  max_applications_per_day: number;
  require_manual_approval: boolean;
  nav_fnr?: string;
  nav_password_encrypted?: string;
  telegram_chat_id?: string;
  telegram_enabled: boolean;
  auto_scan_enabled: boolean;
  scan_interval_hours: number;
  last_scan_at?: string;
  created_at: string;
  updated_at: string;
}

export interface UnifiedProfile {
  comprehensive_summary: string;
  all_work_experience: WorkExperience[];
  comprehensive_skills: Skills;
  education: Education[];
  languages: Language[];
}

export interface WorkExperience {
  period: string;
  role: string;
  company: string;
  description?: string;
}

export interface Skills {
  technical: string[];
  soft_skills: string[];
  languages: Language[];
}

export interface Language {
  language: string;
  spoken: string;
  written?: string;
}

export interface Education {
  institution: string;
  degree: string;
  period: string;
}

export interface Job {
  // Primary identifiers
  id: string;
  user_id: string;
  scan_task_id?: string;

  // Core job information
  title: string;
  company: string;
  location?: string;
  url: string;
  source: 'FINN' | 'NAV';

  // Job details
  description?: string;
  requirements?: string[];
  responsibilities?: string[];
  benefits?: string[];

  // Contact information
  contact_name?: string;
  contact_email?: string;
  contact_phone?: string;

  // Address details
  address?: string;
  city?: string;
  postalCode?: string;
  county?: string;
  country?: string;

  // Employment details
  employment_type?: string;
  extent?: string;
  salary_range?: string;
  start_date?: string;
  deadline?: string;

  // Source-specific fields
  finnkode?: string; // FINN.no job code
  application_url?: string;

  // Skyvern processing
  skyvern_status?: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
  recording_url?: string;
  task_id?: string;
  processing_details?: any;

  // AI Analysis (for job relevance)
  relevance_score?: number;
  ai_analysis?: AIAnalysis;
  match_reasons?: string[];
  concerns?: string[];
  recommendation?: 'APPLY' | 'SKIP' | 'REVIEW';

  // Processing status
  status: 'NEW' | 'REVIEWED' | 'RELEVANT' | 'NOT_RELEVANT' | 'APPROVED' | 'APPLIED' | 'REJECTED' | 'ARCHIVED';
  is_processed: boolean;
  _skip?: boolean;
  _skip_reason?: string;

  // Timestamps
  posted_date?: string;
  scraped_at?: string;
  sistEndret?: string; // Norwegian: last modified
  created_at: string;
  updated_at: string;
  analyzed_at?: string;
  applied_at?: string;

  // Legacy/deprecated fields (for backward compatibility)
  application_form_html?: string;
  skyvern_task_id?: string;
}

export interface AIAnalysis {
  relevance_score: number;
  is_relevant: boolean;
  match_reasons: string[];
  concerns: string[];
  recommendation: 'APPLY' | 'SKIP' | 'REVIEW';
  detailed_analysis?: string;
}

export interface CoverLetter {
  id: string;
  user_id: string;
  job_id: string;
  content: string;
  language: string;
  word_count: number;
  pdf_path?: string;
  txt_path?: string;
  ai_model: string;
  generation_prompt?: string;
  custom_edited: boolean;
  created_at: string;
  updated_at: string;
}

export interface Application {
  id: string;
  user_id: string;
  job_id: string;
  cover_letter_id?: string;
  application_url?: string;
  status: 'PENDING' | 'SUCCESS' | 'FAILED' | 'REPORTED';
  skyvern_result?: SkyvernResult;
  screenshot_path?: string;
  nav_reported: boolean;
  nav_report_date?: string;
  nav_response?: any;
  error_message?: string;
  retry_count: number;
  last_retry_at?: string;
  submitted_at?: string;
  created_at: string;
  updated_at: string;
  // Joined data
  job?: Job;
  cover_letter?: CoverLetter;
}

export interface SkyvernResult {
  success: boolean;
  screenshots: string[];
  errors?: string[];
  duration_seconds?: number;
}

export interface MonitoringLog {
  id: string;
  user_id: string;
  scan_type: 'MANUAL' | 'SCHEDULED' | 'WEBHOOK';
  jobs_found: number;
  jobs_analyzed: number;
  jobs_relevant: number;
  applications_sent: number;
  nav_reports_sent: number;
  status: 'RUNNING' | 'COMPLETED' | 'FAILED';
  error_message?: string;
  details?: any;
  duration_seconds?: number;
  started_at: string;
  completed_at?: string;
}

export interface DashboardStats {
  total_jobs: number;
  new_jobs: number;
  analyzed_jobs: number;
  relevant_jobs: number;
  total_applications: number;
  successful_applications: number;
  nav_reports: number;
  last_scan_at?: string;
}

export interface ActivityData {
  activity_date: string;
  jobs_found: number;
  applications_sent: number;
}

// API Response types
export interface ApiResponse<T> {
  data?: T;
  error?: string;
  message?: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  per_page: number;
}

// API Request types
export interface ScanJobsRequest {
  user_id: string;
  scan_type: 'MANUAL' | 'SCHEDULED';
}

export interface AnalyzeJobRequest {
  job_id: string;
  user_id: string;
}

export interface GenerateCoverLetterRequest {
  job_id: string;
  user_id: string;
  custom_prompt?: string;
}

export interface ApplyToJobRequest {
  application_id: string;
  user_id: string;
}

export interface ReportToNAVRequest {
  application_id: string;
  user_id: string;
}
