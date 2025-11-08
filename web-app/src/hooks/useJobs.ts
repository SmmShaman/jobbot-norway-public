import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { db } from '@/lib/supabase';
import { jobsApi } from '@/lib/api';
import type { Job } from '@/types';

export const useJobs = (userId: string, filters?: any) => {
  return useQuery({
    queryKey: ['jobs', userId, filters],
    queryFn: () => db.getJobs(userId, filters),
    enabled: !!userId,
  });
};

export const useJob = (jobId: string) => {
  return useQuery({
    queryKey: ['job', jobId],
    queryFn: () => db.getJob(jobId),
    enabled: !!jobId,
  });
};

export const useScanJobs = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: jobsApi.scanJobs,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
    },
  });
};

export const useAnalyzeJob = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: jobsApi.analyzeJob,
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['job', variables.job_id] });
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
    },
  });
};

export const useUpdateJob = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ jobId, updates }: { jobId: string; updates: Partial<Job> }) =>
      db.updateJob(jobId, updates),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['job', variables.jobId] });
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
    },
  });
};

export const useApproveJob = () => {
  const { mutate: updateJob } = useUpdateJob();

  return (jobId: string) => {
    updateJob({ jobId, updates: { status: 'APPLIED' } });
  };
};

export const useRejectJob = () => {
  const { mutate: updateJob } = useUpdateJob();

  return (jobId: string) => {
    updateJob({ jobId, updates: { status: 'REJECTED' } });
  };
};
