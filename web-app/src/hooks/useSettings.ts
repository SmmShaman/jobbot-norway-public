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

// AI-parsed resume profile
export const useAIParsedProfile = (userId: string) => {
  return useQuery({
    queryKey: ['aiProfile', userId],
    queryFn: () => db.getUserProfile(userId),
    enabled: !!userId,
  });
};

// Analyze all uploaded resumes with AI
export const useAnalyzeResumes = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ userId }: { userId: string }) => {
      const result = await storage.analyzeResumes(userId);
      return result;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['aiProfile', variables.userId] });
      queryClient.invalidateQueries({ queryKey: ['settings', variables.userId] });
    },
  });
};

// ============================================================
// SAVED PROFILES HOOKS (for job relevance analysis)
// ============================================================

// Get all saved profiles for user
export const useSavedProfiles = (userId: string) => {
  return useQuery({
    queryKey: ['savedProfiles', userId],
    queryFn: () => db.getSavedProfiles(userId),
    enabled: !!userId,
  });
};

// Get active profile (used for job relevance scoring)
export const useActiveProfile = (userId: string) => {
  return useQuery({
    queryKey: ['activeProfile', userId],
    queryFn: () => db.getActiveProfile(userId),
    enabled: !!userId,
  });
};

// Save current profile with optional name
export const useSaveProfile = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      userId,
      profileName,
      profileData,
      sourceResumes,
    }: {
      userId: string;
      profileName: string | null;
      profileData: any;
      sourceResumes: string[];
    }) => {
      const result = await db.saveProfile(userId, profileName, profileData, sourceResumes);
      return result;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['savedProfiles', variables.userId] });
    },
  });
};

// Set active profile (only one can be active at a time)
export const useSetActiveProfile = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ userId, profileId }: { userId: string; profileId: string }) => {
      const result = await db.setActiveProfile(userId, profileId);
      return result;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['savedProfiles', variables.userId] });
      queryClient.invalidateQueries({ queryKey: ['activeProfile', variables.userId] });
    },
  });
};

// Delete saved profile
export const useDeleteProfile = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ profileId }: { profileId: string; userId: string }) => {
      await db.deleteProfile(profileId);
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['savedProfiles', variables.userId] });
      queryClient.invalidateQueries({ queryKey: ['activeProfile', variables.userId] });
    },
  });
};

// Update profile name
export const useUpdateProfileName = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      profileId,
      newName,
    }: {
      profileId: string;
      newName: string;
      userId: string;
    }) => {
      const result = await db.updateProfileName(profileId, newName);
      return result;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['savedProfiles', variables.userId] });
    },
  });
};
