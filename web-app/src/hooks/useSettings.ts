import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { db, storage } from '@/lib/supabase';
import type { UserSettings } from '@/types';

export const useUserSettings = (userId: string) => {
  return useQuery({
    queryKey: ['settings', userId],
    queryFn: () => db.getSettings(userId),
    enabled: !!userId,
  });
};

export const useUpdateSettings = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ userId, updates }: { userId: string; updates: Partial<UserSettings> }) =>
      db.updateSettings(userId, updates),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['settings', variables.userId] });
    },
  });
};

export const useUploadResume = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ userId, file }: { userId: string; file: File }) => {
      const uploadResult = await storage.uploadResume(userId, file);
      return uploadResult;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['settings', variables.userId] });
    },
  });
};

export const useUserProfile = (userId: string) => {
  return useQuery({
    queryKey: ['profile', userId],
    queryFn: () => db.getProfile(userId),
    enabled: !!userId,
  });
};

export const useUpdateProfile = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ userId, updates }: { userId: string; updates: any }) =>
      db.updateProfile(userId, updates),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['profile', variables.userId] });
    },
  });
};
