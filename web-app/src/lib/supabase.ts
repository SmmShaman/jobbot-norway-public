import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error('Missing Supabase environment variables. Check your .env file.');
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    autoRefreshToken: true,
    persistSession: true,
    detectSessionInUrl: true,
  },
});

// Helper functions for common operations
export const auth = {
  signUp: async (email: string, password: string, metadata?: Record<string, any>) => {
    return await supabase.auth.signUp({
      email,
      password,
      options: {
        data: metadata,
      },
    });
  },

  signIn: async (email: string, password: string) => {
    return await supabase.auth.signInWithPassword({
      email,
      password,
    });
  },

  signOut: async () => {
    return await supabase.auth.signOut();
  },

  getCurrentUser: async () => {
    const { data: { user } } = await supabase.auth.getUser();
    return user;
  },

  onAuthStateChange: (callback: (event: string, session: any) => void) => {
    return supabase.auth.onAuthStateChange(callback);
  },
};

// Storage helpers
export const storage = {
  uploadResume: async (userId: string, file: File) => {
    const fileExt = file.name.split('.').pop();
    const fileName = `${userId}/resume_${Date.now()}.${fileExt}`;

    const { data, error } = await supabase.storage
      .from('resumes')
      .upload(fileName, file, {
        cacheControl: '3600',
        upsert: true,
      });

    if (error) throw error;
    return data;
  },

  getResumeUrl: async (path: string) => {
    const { data } = await supabase.storage
      .from('resumes')
      .createSignedUrl(path, 3600); // 1 hour expiry

    return data?.signedUrl;
  },

  uploadScreenshot: async (userId: string, applicationId: string, file: Blob) => {
    const fileName = `${userId}/applications/${applicationId}/screenshot_${Date.now()}.png`;

    const { data, error } = await supabase.storage
      .from('screenshots')
      .upload(fileName, file);

    if (error) throw error;
    return data;
  },
};

// Database helpers with RLS
export const db = {
  // Profile operations
  getProfile: async (userId: string) => {
    const { data, error } = await supabase
      .from('profiles')
      .select('*')
      .eq('id', userId)
      .single();

    if (error) throw error;
    return data;
  },

  updateProfile: async (userId: string, updates: Partial<any>) => {
    const { data, error } = await supabase
      .from('profiles')
      .update(updates)
      .eq('id', userId)
      .select()
      .single();

    if (error) throw error;
    return data;
  },

  // Settings operations
  getSettings: async (userId: string) => {
    const { data, error } = await supabase
      .from('user_settings')
      .select('*')
      .eq('user_id', userId)
      .single();

    if (error) throw error;
    return data;
  },

  updateSettings: async (userId: string, updates: Partial<any>) => {
    const { data, error } = await supabase
      .from('user_settings')
      .update(updates)
      .eq('user_id', userId)
      .select()
      .single();

    if (error) throw error;
    return data;
  },

  // Jobs operations
  getJobs: async (userId: string, filters?: any) => {
    let query = supabase
      .from('jobs')
      .select('*')
      .eq('user_id', userId)
      .order('created_at', { ascending: false });

    if (filters?.status) {
      query = query.eq('status', filters.status);
    }

    if (filters?.min_relevance) {
      query = query.gte('relevance_score', filters.min_relevance);
    }

    const { data, error } = await query;
    if (error) throw error;
    return data;
  },

  getJob: async (jobId: string) => {
    const { data, error } = await supabase
      .from('jobs')
      .select('*')
      .eq('id', jobId)
      .single();

    if (error) throw error;
    return data;
  },

  updateJob: async (jobId: string, updates: Partial<any>) => {
    const { data, error } = await supabase
      .from('jobs')
      .update(updates)
      .eq('id', jobId)
      .select()
      .single();

    if (error) throw error;
    return data;
  },

  // Applications operations
  getApplications: async (userId: string) => {
    const { data, error } = await supabase
      .from('applications')
      .select(`
        *,
        job:jobs(*),
        cover_letter:cover_letters(*)
      `)
      .eq('user_id', userId)
      .order('created_at', { ascending: false });

    if (error) throw error;
    return data;
  },

  createApplication: async (application: any) => {
    const { data, error } = await supabase
      .from('applications')
      .insert(application)
      .select()
      .single();

    if (error) throw error;
    return data;
  },

  // Cover letters operations
  getCoverLetter: async (jobId: string) => {
    const { data, error } = await supabase
      .from('cover_letters')
      .select('*')
      .eq('job_id', jobId)
      .single();

    if (error) throw error;
    return data;
  },

  createCoverLetter: async (coverLetter: any) => {
    const { data, error } = await supabase
      .from('cover_letters')
      .insert(coverLetter)
      .select()
      .single();

    if (error) throw error;
    return data;
  },

  updateCoverLetter: async (id: string, updates: Partial<any>) => {
    const { data, error } = await supabase
      .from('cover_letters')
      .update(updates)
      .eq('id', id)
      .select()
      .single();

    if (error) throw error;
    return data;
  },

  // Dashboard stats
  getDashboardStats: async (userId: string) => {
    const { data, error } = await supabase
      .from('user_dashboard_stats')
      .select('*')
      .eq('user_id', userId)
      .single();

    if (error) throw error;
    return data;
  },

  // Monitoring logs
  getMonitoringLogs: async (userId: string, limit = 10) => {
    const { data, error } = await supabase
      .from('monitoring_logs')
      .select('*')
      .eq('user_id', userId)
      .order('started_at', { ascending: false })
      .limit(limit);

    if (error) throw error;
    return data;
  },

  createMonitoringLog: async (log: any) => {
    const { data, error } = await supabase
      .from('monitoring_logs')
      .insert(log)
      .select()
      .single();

    if (error) throw error;
    return data;
  },
};

// Realtime subscriptions
export const subscribeToJobs = (userId: string, callback: (payload: any) => void) => {
  return supabase
    .channel('jobs_changes')
    .on(
      'postgres_changes',
      {
        event: '*',
        schema: 'public',
        table: 'jobs',
        filter: `user_id=eq.${userId}`,
      },
      callback
    )
    .subscribe();
};

export const subscribeToApplications = (userId: string, callback: (payload: any) => void) => {
  return supabase
    .channel('applications_changes')
    .on(
      'postgres_changes',
      {
        event: '*',
        schema: 'public',
        table: 'applications',
        filter: `user_id=eq.${userId}`,
      },
      callback
    )
    .subscribe();
};
