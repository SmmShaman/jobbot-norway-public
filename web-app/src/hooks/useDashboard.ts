import { useQuery } from '@tanstack/react-query';
import { db } from '@/lib/supabase';

export const useDashboardStats = (userId: string) => {
  return useQuery({
    queryKey: ['dashboard', 'stats', userId],
    queryFn: () => db.getDashboardStats(userId),
    enabled: !!userId,
    refetchInterval: 30000, // Refresh every 30 seconds
  });
};

export const useMonitoringLogs = (userId: string, limit = 10) => {
  return useQuery({
    queryKey: ['monitoring', 'logs', userId],
    queryFn: () => db.getMonitoringLogs(userId, limit),
    enabled: !!userId,
  });
};
