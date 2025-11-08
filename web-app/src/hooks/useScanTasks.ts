import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { supabase } from '@/lib/supabase';

export interface ScanTask {
  id: string;
  user_id: string;
  url: string;
  source: 'FINN' | 'NAV';
  scan_type: 'MANUAL' | 'SCHEDULED' | 'QUICK';
  status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
  worker_id?: string;
  started_at?: string;
  completed_at?: string;
  jobs_found: number;
  jobs_saved: number;
  error_message?: string;
  retry_count: number;
  max_retries: number;
  created_at: string;
  updated_at: string;
}

export const useScanTasks = (userId: string, limit = 10) => {
  return useQuery({
    queryKey: ['scan_tasks', userId],
    queryFn: async () => {
      const { data, error } = await supabase
        .from('scan_tasks')
        .select('*')
        .eq('user_id', userId)
        .order('created_at', { ascending: false })
        .limit(limit);

      if (error) throw error;
      return data as ScanTask[];
    },
    enabled: !!userId,
    refetchInterval: 3000, // Refresh every 3 seconds
  });
};

export const useActiveScanTasks = (userId: string) => {
  return useQuery({
    queryKey: ['scan_tasks', 'active', userId],
    queryFn: async () => {
      const { data, error } = await supabase
        .from('scan_tasks')
        .select('*')
        .eq('user_id', userId)
        .in('status', ['PENDING', 'PROCESSING'])
        .order('created_at', { ascending: false });

      if (error) throw error;
      return data as ScanTask[];
    },
    enabled: !!userId,
    refetchInterval: 2000, // Refresh every 2 seconds for active tasks
  });
};

export const useScanTaskStats = (userId: string) => {
  return useQuery({
    queryKey: ['scan_tasks', 'stats', userId],
    queryFn: async () => {
      const { data, error } = await supabase
        .from('scan_tasks')
        .select('status, jobs_found, jobs_saved')
        .eq('user_id', userId);

      if (error) throw error;

      const stats = {
        total: data.length,
        pending: data.filter((t) => t.status === 'PENDING').length,
        processing: data.filter((t) => t.status === 'PROCESSING').length,
        completed: data.filter((t) => t.status === 'COMPLETED').length,
        failed: data.filter((t) => t.status === 'FAILED').length,
        total_jobs_found: data.reduce((sum, t) => sum + (t.jobs_found || 0), 0),
        total_jobs_saved: data.reduce((sum, t) => sum + (t.jobs_saved || 0), 0),
      };

      return stats;
    },
    enabled: !!userId,
    refetchInterval: 5000, // Refresh every 5 seconds
  });
};

// Mutation: Cancel/Pause scan task
export const useCancelScanTask = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (taskId: string) => {
      const { data, error } = await supabase
        .from('scan_tasks')
        .update({
          status: 'FAILED',
          error_message: 'Cancelled by user',
          completed_at: new Date().toISOString()
        })
        .eq('id', taskId)
        .select()
        .single();

      if (error) throw error;
      return data;
    },
    onSuccess: () => {
      // Invalidate and refetch scan tasks
      queryClient.invalidateQueries({ queryKey: ['scan_tasks'] });
    },
  });
};

// Mutation: Delete scan task
export const useDeleteScanTask = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (taskId: string) => {
      const { error } = await supabase
        .from('scan_tasks')
        .delete()
        .eq('id', taskId);

      if (error) throw error;
      return taskId;
    },
    onSuccess: () => {
      // Invalidate and refetch scan tasks
      queryClient.invalidateQueries({ queryKey: ['scan_tasks'] });
    },
  });
};

// Mutation: Create new scan task
export const useCreateScanTask = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (params: { user_id: string; url: string; scan_type: 'MANUAL' | 'SCHEDULED' | 'QUICK'; source?: 'FINN' | 'NAV' }) => {
      // Auto-detect source from URL if not provided
      let source = params.source;
      if (!source) {
        if (params.url.includes('finn.no')) {
          source = 'FINN';
        } else if (params.url.includes('nav.no') || params.url.includes('arbeidsplassen.nav.no')) {
          source = 'NAV';
        } else {
          source = 'FINN'; // Default to FINN
        }
      }

      const { data, error } = await supabase
        .from('scan_tasks')
        .insert({
          user_id: params.user_id,
          url: params.url,
          scan_type: params.scan_type,
          source,
          status: 'PENDING',
          jobs_found: 0,
          jobs_saved: 0,
          retry_count: 0,
          max_retries: 3,
        })
        .select()
        .single();

      if (error) throw error;
      return data;
    },
    onSuccess: () => {
      // Invalidate and refetch scan tasks
      queryClient.invalidateQueries({ queryKey: ['scan_tasks'] });
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
    },
  });
};
