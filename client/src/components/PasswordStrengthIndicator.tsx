/**
 * Password Strength Indicator Component
 * Provides real-time visual feedback on password strength
 */

import { useMemo } from 'react';
import { cn } from '@/lib/utils';
import { CheckCircle2, XCircle } from 'lucide-react';

interface PasswordStrengthIndicatorProps {
  password: string;
  className?: string;
}

interface StrengthCheck {
  label: string;
  test: (password: string) => boolean;
}

const checks: StrengthCheck[] = [
  { label: 'At least 12 characters', test: (pwd) => pwd.length >= 12 },
  { label: 'Contains uppercase letter', test: (pwd) => /[A-Z]/.test(pwd) },
  { label: 'Contains lowercase letter', test: (pwd) => /[a-z]/.test(pwd) },
  { label: 'Contains number', test: (pwd) => /[0-9]/.test(pwd) },
  { label: 'Contains special character', test: (pwd) => /[!@#$%^&*(),.?":{}|<>]/.test(pwd) },
  { label: 'No spaces', test: (pwd) => !/\s/.test(pwd) },
];

export function PasswordStrengthIndicator({ password, className }: PasswordStrengthIndicatorProps) {
  const strength = useMemo(() => {
    if (!password) return { score: 0, label: '', color: '' };

    const passedChecks = checks.filter(check => check.test(password)).length;
    const totalChecks = checks.length;
    const score = passedChecks / totalChecks;

    if (score < 0.5) {
      return { score, label: 'Weak', color: 'text-red-500' };
    } else if (score < 0.8) {
      return { score, label: 'Medium', color: 'text-yellow-500' };
    } else {
      return { score, label: 'Strong', color: 'text-green-500' };
    }
  }, [password]);

  const passedChecks = useMemo(() => {
    return checks.filter(check => check.test(password));
  }, [password]);

  if (!password) return null;

  return (
    <div className={cn('space-y-2', className)}>
      <div className="flex items-center justify-between text-sm">
        <span className="text-muted-foreground">Password strength:</span>
        <span className={cn('font-semibold', strength.color)}>{strength.label}</span>
      </div>
      
      {/* Strength bar */}
      <div className="h-2 bg-muted rounded-full overflow-hidden">
        <div
          className={cn(
            'h-full transition-all duration-300',
            strength.score < 0.5 && 'bg-red-500',
            strength.score >= 0.5 && strength.score < 0.8 && 'bg-yellow-500',
            strength.score >= 0.8 && 'bg-green-500'
          )}
          style={{ width: `${strength.score * 100}%` }}
        />
      </div>

      {/* Requirements checklist */}
      <div className="space-y-1.5 text-xs">
        {checks.map((check, index) => {
          const passed = check.test(password);
          return (
            <div key={index} className="flex items-center gap-2">
              {passed ? (
                <CheckCircle2 className="h-3.5 w-3.5 text-green-500 flex-shrink-0" />
              ) : (
                <XCircle className="h-3.5 w-3.5 text-muted-foreground flex-shrink-0" />
              )}
              <span className={cn(passed ? 'text-green-600 dark:text-green-400' : 'text-muted-foreground')}>
                {check.label}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

