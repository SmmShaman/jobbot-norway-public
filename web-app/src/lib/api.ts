import axios from 'axios';
import { supabase } from './supabase';
import type {
  ApiResponse,
  ScanJobsRequest,
  AnalyzeJobRequest,
  GenerateCoverLetterRequest,
  ApplyToJobRequest,
  ReportToNAVRequest,
} from '@/types';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('supabase.auth.token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const jobsApi = {
  // Trigger job scanning - Create scan task directly in Supabase
  scanJobs: async (request: ScanJobsRequest): Promise<ApiResponse<any>> => {
    try {
      // Get user settings to fetch search URLs
      const { data: settings, error: settingsError } = await supabase
        .from('user_settings')
        .select('finn_search_urls, nav_search_urls')
        .eq('user_id', request.user_id)
        .single();

      if (settingsError) throw settingsError;

      const searchUrls = settings?.finn_search_urls || [];

      if (searchUrls.length === 0) {
        throw new Error('No search URLs configured. Please add search URLs in Settings.');
      }

      // Create scan task for each URL with PENDING status
      const tasks = await Promise.all(
        searchUrls.map(async (url: string) => {
          const { data, error } = await supabase
            .from('scan_tasks')
            .insert({
              user_id: request.user_id,
              url: url,
              source: 'FINN',
              scan_type: request.scan_type || 'MANUAL',
              status: 'PENDING', // Worker looks for PENDING status
              max_retries: 3,
              retry_count: 0
            })
            .select()
            .single();

          if (error) throw error;
          return data;
        })
      );

      return {
        success: true,
        data: tasks,
        message: `Created ${tasks.length} scan task(s). Worker will process them shortly.`
      };
    } catch (error: any) {
      return {
        success: false,
        error: error.message,
        message: 'Failed to create scan tasks'
      };
    }
  },

  // Analyze single job with AI
  analyzeJob: async (request: AnalyzeJobRequest): Promise<ApiResponse<any>> => {
    const { data } = await api.post('/api/analyze-job', request);
    return data;
  },

  // Batch analyze jobs
  batchAnalyzeJobs: async (userId: string, jobIds: string[]): Promise<ApiResponse<any>> => {
    const { data } = await api.post('/api/batch-analyze', { user_id: userId, job_ids: jobIds });
    return data;
  },
};

export const coverLettersApi = {
  // Generate cover letter with AI
  generate: async (request: GenerateCoverLetterRequest): Promise<ApiResponse<any>> => {
    const { data } = await api.post('/api/generate-letter', request);
    return data;
  },

  // Regenerate with custom prompt
  regenerate: async (coverLetterId: string, customPrompt: string): Promise<ApiResponse<any>> => {
    const { data } = await api.post(`/api/regenerate-letter/${coverLetterId}`, {
      custom_prompt: customPrompt,
    });
    return data;
  },
};

export const applicationsApi = {
  // Fill and submit application form
  applyToJob: async (request: ApplyToJobRequest): Promise<ApiResponse<any>> => {
    const { data } = await api.post('/api/apply', request);
    return data;
  },

  // Get application status
  getStatus: async (applicationId: string): Promise<ApiResponse<any>> => {
    const { data } = await api.get(`/api/applications/${applicationId}/status`);
    return data;
  },

  // Retry failed application
  retry: async (applicationId: string): Promise<ApiResponse<any>> => {
    const { data } = await api.post(`/api/applications/${applicationId}/retry`);
    return data;
  },
};

export const navApi = {
  // Report application to NAV
  reportToNav: async (request: ReportToNAVRequest): Promise<ApiResponse<any>> => {
    const { data } = await api.post('/api/report-nav', request);
    return data;
  },

  // Test NAV credentials
  testCredentials: async (userId: string): Promise<ApiResponse<any>> => {
    const { data } = await api.post('/api/test-nav-credentials', { user_id: userId });
    return data;
  },
};

export const resumeApi = {
  // Analyze uploaded resume
  analyze: async (userId: string, resumePath: string): Promise<ApiResponse<any>> => {
    const { data } = await api.post('/api/analyze-resume', {
      user_id: userId,
      resume_path: resumePath,
    });
    return data;
  },
};

export const monitoringApi = {
  // Get monitoring status
  getStatus: async (userId: string): Promise<ApiResponse<any>> => {
    const { data } = await api.get(`/api/monitoring/status/${userId}`);
    return data;
  },

  // Start monitoring
  startMonitoring: async (userId: string): Promise<ApiResponse<any>> => {
    const { data } = await api.post('/api/monitoring/start', { user_id: userId });
    return data;
  },

  // Stop monitoring
  stopMonitoring: async (userId: string): Promise<ApiResponse<any>> => {
    const { data } = await api.post('/api/monitoring/stop', { user_id: userId });
    return data;
  },
};

export default api;
