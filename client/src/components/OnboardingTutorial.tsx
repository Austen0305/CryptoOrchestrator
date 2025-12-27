/**
 * Onboarding Tutorial Component
 * Interactive step-by-step tutorial for new users
 */

import React, { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  CheckCircle2,
  Circle,
  SkipForward,
  X,
  ArrowRight,
  ArrowLeft,
  Trophy,
} from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import {
  useOnboardingProgress,
  useCompleteStep,
  useSkipStep,
  useResetOnboarding,
  useAchievements,
  type OnboardingProgress as OnboardingProgressType,
} from "@/hooks/useOnboarding";

const ONBOARDING_STEPS = [
  {
    id: "welcome",
    title: "Welcome to CryptoOrchestrator",
    description: "Let's get you started with your crypto trading journey",
    icon: "👋",
  },
  {
    id: "wallet_setup",
    title: "Set Up Your Wallet",
    description: "Create or connect your wallet to start trading",
    icon: "💼",
  },
  {
    id: "first_deposit",
    title: "Make Your First Deposit",
    description: "Add funds to your wallet to begin trading",
    icon: "💰",
  },
  {
    id: "first_trade",
    title: "Place Your First Trade",
    description: "Execute your first trade and learn the basics",
    icon: "📈",
  },
  {
    id: "bot_creation",
    title: "Create a Trading Bot",
    description: "Automate your trading with AI-powered bots",
    icon: "🤖",
  },
  {
    id: "marketplace_explore",
    title: "Explore the Marketplace",
    description: "Discover copy trading and custom indicators",
    icon: "🛒",
  },
  {
    id: "advanced_features",
    title: "Advanced Features",
    description: "Unlock powerful tools for experienced traders",
    icon: "⚡",
  },
];

export function OnboardingTutorial() {
  const [isOpen, setIsOpen] = useState(false);
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const { toast } = useToast();

  const { data: progress, isLoading } = useOnboardingProgress();
  const { data: achievements } = useAchievements();
  const completeStep = useCompleteStep();
  const skipStep = useSkipStep();
  const resetOnboarding = useResetOnboarding();

  // Determine current step from progress
  useEffect(() => {
    if (progress?.current_step) {
      const stepIndex = ONBOARDING_STEPS.findIndex((s) => s.id === progress.current_step);
      if (stepIndex >= 0) {
        setCurrentStepIndex(stepIndex);
      }
    }
  }, [progress]);

  // Auto-open if not completed
  useEffect(() => {
    if (progress && !progress.is_completed && !isOpen) {
      setIsOpen(true);
    }
  }, [progress, isOpen]);

  const currentStep = ONBOARDING_STEPS[currentStepIndex];
  const isStepCompleted = (stepId: string) =>
    progress?.completed_steps?.[stepId] !== undefined;
  const isStepSkipped = (stepId: string) => progress?.skipped_steps?.[stepId] !== undefined;

  const handleComplete = async () => {
    if (!currentStep) return;
    try {
      await completeStep.mutateAsync(currentStep.id);
      toast({
        title: "Step completed!",
        description: `Great job completing: ${currentStep.title}`,
      });

      // Move to next step
      if (currentStepIndex < ONBOARDING_STEPS.length - 1) {
        setCurrentStepIndex(currentStepIndex + 1);
      } else {
        setIsOpen(false);
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to complete step",
        variant: "destructive",
      });
    }
  };

  const handleSkip = async () => {
    if (!currentStep) return;
    try {
      await skipStep.mutateAsync(currentStep.id);
      toast({
        title: "Step skipped",
        description: "You can complete this later",
      });

      // Move to next step
      if (currentStepIndex < ONBOARDING_STEPS.length - 1) {
        setCurrentStepIndex(currentStepIndex + 1);
      } else {
        setIsOpen(false);
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to skip step",
        variant: "destructive",
      });
    }
  };

  const handleClose = () => {
    setIsOpen(false);
  };

  if (isLoading) {
    return null;
  }

  if (progress?.is_completed) {
    return null; // Don't show if completed
  }

  if (!currentStep) {
    return null;
  }

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <span className="text-2xl">{currentStep.icon}</span>
            {currentStep.title}
          </DialogTitle>
          <DialogDescription>{currentStep.description}</DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Progress Bar */}
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span>Progress</span>
              <span>{progress?.progress_percentage || 0}%</span>
            </div>
            <Progress value={progress?.progress_percentage || 0} />
          </div>

          {/* Step List */}
          <div className="space-y-2">
            {ONBOARDING_STEPS.map((step, index) => (
              <div
                key={step.id}
                className={`flex items-center gap-3 p-2 rounded ${
                  index === currentStepIndex ? "bg-primary/10" : ""
                }`}
              >
                {isStepCompleted(step.id) ? (
                  <CheckCircle2 className="h-5 w-5 text-green-500" />
                ) : isStepSkipped(step.id) ? (
                  <SkipForward className="h-5 w-5 text-yellow-500" />
                ) : (
                  <Circle className="h-5 w-5 text-gray-400" />
                )}
                <span className="flex-1">{step.title}</span>
                {index === currentStepIndex && (
                  <Badge variant="default">Current</Badge>
                )}
              </div>
            ))}
          </div>

          {/* Achievements Preview */}
          {achievements && achievements.length > 0 && (
            <div className="border-t pt-4">
              <h4 className="text-sm font-semibold mb-2 flex items-center gap-2">
                <Trophy className="h-4 w-4" />
                Achievements Unlocked
              </h4>
              <div className="flex flex-wrap gap-2">
                {achievements
                  .filter((a) => a.is_unlocked)
                  .map((achievement) => (
                    <Badge key={achievement.id} variant="secondary">
                      {achievement.achievement_name}
                    </Badge>
                  ))}
              </div>
            </div>
          )}
        </div>

        <DialogFooter className="flex justify-between">
          <div className="flex gap-2">
            <Button variant="outline" onClick={handleSkip} disabled={completeStep.isPending}>
              <SkipForward className="h-4 w-4 mr-2" />
              Skip
            </Button>
            {currentStepIndex > 0 && (
              <Button
                variant="outline"
                onClick={() => setCurrentStepIndex(currentStepIndex - 1)}
              >
                <ArrowLeft className="h-4 w-4 mr-2" />
                Previous
              </Button>
            )}
          </div>
          <div className="flex gap-2">
            <Button variant="ghost" onClick={handleClose}>
              Close
            </Button>
            <Button onClick={handleComplete} disabled={completeStep.isPending}>
              {completeStep.isPending ? (
                "Completing..."
              ) : currentStepIndex === ONBOARDING_STEPS.length - 1 ? (
                "Finish"
              ) : (
                <>
                  Complete & Continue
                  <ArrowRight className="h-4 w-4 ml-2" />
                </>
              )}
            </Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

/**
 * Achievement Badge Component
 */
export function AchievementBadge({ achievementId }: { achievementId: string }) {
  const { data: achievements } = useAchievements();
  const achievement = achievements?.find((a) => a.achievement_id === achievementId);

  if (!achievement || !achievement.is_unlocked) {
    return null;
  }

  return (
    <Badge variant="secondary" className="flex items-center gap-1">
      <Trophy className="h-3 w-3" />
      {achievement.achievement_name}
    </Badge>
  );
}

