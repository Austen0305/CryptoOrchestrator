/**
 * React Query hooks for user onboarding
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiRequest } from "@/lib/queryClient";

export interface OnboardingProgress {
  user_id: number;
  current_step: string | null;
  completed_steps: Record<string, string>;
  skipped_steps: Record<string, string>;
  progress_percentage: number;
  total_steps: number;
  is_completed: boolean;
  completed_at: string | null;
}

export interface UserAchievement {
  id: number;
  achievement_id: string;
  achievement_name: string;
  achievement_description: string | null;
  progress: number;
  max_progress: number;
  is_unlocked: boolean;
  unlocked_at: string | null;
}

export const onboardingApi = {
  getProgress: () =>
    apiRequest<OnboardingProgress>("/api/onboarding/progress", { method: "GET" }),

  completeStep: (stepId: string) =>
    apiRequest<OnboardingProgress>("/api/onboarding/complete-step", {
      method: "POST",
      body: { step_id: stepId },
    }),

  skipStep: (stepId: string) =>
    apiRequest<OnboardingProgress>("/api/onboarding/skip-step", {
      method: "POST",
      body: { step_id: stepId },
    }),

  reset: () =>
    apiRequest<{ success: boolean; message: string }>("/api/onboarding/reset", {
      method: "POST",
    }),

  getAchievements: () =>
    apiRequest<UserAchievement[]>("/api/onboarding/achievements", { method: "GET" }),
};

/**
 * Hook to get onboarding progress
 */
export function useOnboardingProgress() {
  return useQuery({
    queryKey: ["onboarding", "progress"],
    queryFn: onboardingApi.getProgress,
  });
}

/**
 * Hook to complete an onboarding step
 */
export function useCompleteStep() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: onboardingApi.completeStep,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["onboarding"] });
    },
  });
}

/**
 * Hook to skip an onboarding step
 */
export function useSkipStep() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: onboardingApi.skipStep,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["onboarding"] });
    },
  });
}

/**
 * Hook to reset onboarding progress
 */
export function useResetOnboarding() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: onboardingApi.reset,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["onboarding"] });
    },
  });
}

/**
 * Hook to get user achievements
 */
export function useAchievements() {
  return useQuery({
    queryKey: ["onboarding", "achievements"],
    queryFn: onboardingApi.getAchievements,
  });
}

