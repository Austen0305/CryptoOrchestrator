import { useState, useLayoutEffect, useEffect } from "react";
import { useLocation } from "wouter";
import { useAuth } from "@/hooks/useAuth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { PasswordStrengthIndicator } from "@/components/PasswordStrengthIndicator";
import { Loader2, Eye, EyeOff, UserPlus } from "lucide-react";
import { Link } from "wouter";
import { useToast } from "@/hooks/use-toast";
import { enableLandingPageScroll } from "@/lib/enableLandingPageScroll";

// Force enable scrolling - call this function to ensure scroll is enabled
function forceEnableScroll() {
  // Ensure landing-page-active class is set FIRST
  document.body.classList.add("landing-page-active");
  document.documentElement.classList.add("landing-page-active");
  
  const root = document.getElementById("root");
  if (root) {
    root.classList.add("landing-page-active");
    // Clear any scroll lock styles from root
    root.style.cssText = "";
  }
  
  // Call the utility function
  enableLandingPageScroll();
  
  // Force set styles with !important to override any scroll lock
  // Use setProperty with important flag
  document.documentElement.style.setProperty("overflow-y", "auto", "important");
  document.documentElement.style.setProperty("overflow", "auto", "important");
  document.documentElement.style.setProperty("height", "auto", "important");
  document.body.style.setProperty("overflow-y", "auto", "important");
  document.body.style.setProperty("overflow", "auto", "important");
  document.body.style.setProperty("height", "auto", "important");
}

export default function Register() {
  const [, setLocation] = useLocation();
  const { register, isLoading, error } = useAuth();
  const { toast } = useToast();

  // Ensure scrolling is enabled synchronously before browser paint
  useLayoutEffect(() => {
    forceEnableScroll();
  }, []);

  // Also enable scrolling after render to override any scroll lock that runs later
  useEffect(() => {
    // Run immediately
    forceEnableScroll();
    
    // Run multiple times with delays to catch scroll lock that runs at different times
    const timers = [
      setTimeout(() => forceEnableScroll(), 0),
      setTimeout(() => forceEnableScroll(), 50),
      setTimeout(() => forceEnableScroll(), 100),
      setTimeout(() => forceEnableScroll(), 200),
      setTimeout(() => forceEnableScroll(), 300),
    ];
    
    // Watch for style changes and re-enable scroll if it gets locked
    const observer = new MutationObserver(() => {
      // Check computed styles to see if scroll is locked
      const htmlStyle = window.getComputedStyle(document.documentElement);
      const bodyStyle = window.getComputedStyle(document.body);
      
      // If overflow is hidden, re-enable scroll
      if (htmlStyle.overflowY === "hidden" || bodyStyle.overflowY === "hidden") {
        forceEnableScroll();
      }
    });
    
    // Observe body and html for style and class changes
    observer.observe(document.body, {
      attributes: true,
      attributeFilter: ["style", "class"],
    });
    
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["style", "class"],
    });
    
    return () => {
      timers.forEach(timer => clearTimeout(timer));
      observer.disconnect();
    };
  }, []);
  const [formData, setFormData] = useState({
    fullName: "",
    email: "",
    username: "",
    password: "",
    confirmPassword: "",
    acceptTerms: false,
  });
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  // Split full name into first and last name intelligently
  const splitFullName = (fullName: string) => {
    const trimmed = fullName.trim();
    if (!trimmed) return { firstName: "", lastName: "" };
    
    const parts = trimmed.split(/\s+/).filter(part => part.length > 0);
    if (parts.length === 0) return { firstName: "", lastName: "" };
    if (parts.length === 1) return { firstName: parts[0], lastName: "" };
    
    // First word is first name, rest is last name
    return {
      firstName: parts[0],
      lastName: parts.slice(1).join(" "),
    };
  };

  const validateForm = () => {
    const errors: Record<string, string> = {};

    // Full name validation - allow spaces
    if (!formData.fullName || formData.fullName.trim().length < 2) {
      errors.fullName = "Please enter your full name (at least 2 characters)";
    } else if (formData.fullName.trim().length > 100) {
      errors.fullName = "Name is too long (maximum 100 characters)";
    }

    // Email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!formData.email || !emailRegex.test(formData.email)) {
      errors.email = "Please enter a valid email address";
    }

    // Username validation
    if (!formData.username || formData.username.length < 3) {
      errors.username = "Username must be at least 3 characters";
    } else if (formData.username.length > 30) {
      errors.username = "Username is too long (maximum 30 characters)";
    } else if (!/^[a-zA-Z0-9_-]+$/.test(formData.username)) {
      errors.username = "Username can only contain letters, numbers, underscores, and hyphens";
    }

    // Password validation - minimum 12 characters
    if (!formData.password || formData.password.length < 12) {
      errors.password = "Password must be at least 12 characters long";
    } else {
      const hasUpperCase = /[A-Z]/.test(formData.password);
      const hasLowerCase = /[a-z]/.test(formData.password);
      const hasNumber = /[0-9]/.test(formData.password);
      const hasSpecial = /[!@#$%^&*(),.?":{}|<>]/.test(formData.password);
      const hasNoSpaces = !/\s/.test(formData.password);

      if (!hasUpperCase || !hasLowerCase || !hasNumber || !hasSpecial) {
        errors.password = "Password must contain uppercase, lowercase, numbers, and special characters";
      } else if (!hasNoSpaces) {
        errors.password = "Password cannot contain spaces";
      }
    }

    // Confirm password
    if (formData.password !== formData.confirmPassword) {
      errors.confirmPassword = "Passwords do not match";
    }

    // Terms acceptance
    if (!formData.acceptTerms) {
      errors.acceptTerms = "You must accept the terms and conditions";
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    const { firstName, lastName } = splitFullName(formData.fullName);

    const success = await register(
      formData.email,
      formData.username,
      formData.password,
      firstName,
      lastName
    );

    if (success) {
      toast({
        title: "Account created successfully!",
        description: "Welcome to CryptoOrchestrator. Redirecting to dashboard...",
        variant: "default",
      });
      setTimeout(() => {
        setLocation("/dashboard");
      }, 1000);
    }
  };

  const handleChange = (field: string, value: string | boolean) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    
    // Clear validation error for this field when user types
    if (validationErrors[field]) {
      setValidationErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }
    
    // Real-time validation
    if (typeof value === 'string') {
      const errors: Record<string, string> = {};
      
      if (field === 'fullName') {
        if (value && value.trim().length < 2) {
          errors.fullName = "Please enter your full name (at least 2 characters)";
        } else if (value && value.trim().length > 100) {
          errors.fullName = "Name is too long (maximum 100 characters)";
        }
      } else if (field === 'email') {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (value && !emailRegex.test(value)) {
          errors.email = "Please enter a valid email address";
        }
      } else if (field === 'username') {
        if (value && value.length < 3) {
          errors.username = "Username must be at least 3 characters";
        } else if (value && value.length > 30) {
          errors.username = "Username is too long (maximum 30 characters)";
        } else if (value && !/^[a-zA-Z0-9_-]+$/.test(value)) {
          errors.username = "Username can only contain letters, numbers, underscores, and hyphens";
        }
      } else if (field === 'password') {
        if (value && value.length < 12) {
          errors.password = "Password must be at least 12 characters long";
        } else if (value) {
          const hasUpperCase = /[A-Z]/.test(value);
          const hasLowerCase = /[a-z]/.test(value);
          const hasNumber = /[0-9]/.test(value);
          const hasSpecial = /[!@#$%^&*(),.?":{}|<>]/.test(value);
          const hasNoSpaces = !/\s/.test(value);
          if (!hasUpperCase || !hasLowerCase || !hasNumber || !hasSpecial) {
            errors.password = "Password must contain uppercase, lowercase, numbers, and special characters";
          } else if (!hasNoSpaces) {
            errors.password = "Password cannot contain spaces";
          }
        }
      } else if (field === 'confirmPassword') {
        if (value && formData.password && value !== formData.password) {
          errors.confirmPassword = "Passwords do not match";
        }
      }
      
      // Re-validate confirmPassword when password changes
      if (field === 'password' && formData.confirmPassword) {
        if (formData.confirmPassword !== value) {
          errors.confirmPassword = "Passwords do not match";
        } else {
          setValidationErrors((prev) => {
            const newErrors = { ...prev };
            delete newErrors.confirmPassword;
            return newErrors;
          });
        }
      }
      
      // Update validation errors
      setValidationErrors((prev) => {
        const newErrors = { ...prev };
        if (errors[field]) {
          newErrors[field] = errors[field];
        } else if (newErrors[field]) {
          delete newErrors[field];
        }
        if (errors.confirmPassword) {
          newErrors.confirmPassword = errors.confirmPassword;
        }
        return newErrors;
      });
    } else if (field === 'acceptTerms') {
      if (value && validationErrors.acceptTerms) {
        setValidationErrors((prev) => {
          const newErrors = { ...prev };
          delete newErrors.acceptTerms;
          return newErrors;
        });
      }
    }
  };

  const isFormValid = () => {
    if (isLoading) return false;
    if (!formData.fullName.trim() || !formData.email || !formData.username || !formData.password || !formData.acceptTerms) {
      return false;
    }
    if (Object.keys(validationErrors).length > 0) {
      return false;
    }
    if (formData.password !== formData.confirmPassword) {
      return false;
    }
    return true;
  };

  return (
    <div className="min-h-screen w-full flex items-center justify-center bg-gradient-to-br from-background via-background to-muted/20 p-4 sm:p-6 py-8 sm:py-12 overflow-y-auto">
      <Card className="w-full max-w-md border-card-border shadow-xl animate-fade-in-up my-8">
        <CardHeader className="space-y-2 text-center">
          <div className="flex justify-center mb-2">
            <div className="p-3 rounded-full bg-primary/10">
              <UserPlus className="h-6 w-6 text-primary" />
            </div>
          </div>
          <CardTitle className="text-2xl md:text-3xl font-bold bg-gradient-to-r from-primary to-primary/80 bg-clip-text text-transparent">
            Create an account
          </CardTitle>
          <CardDescription className="text-sm md:text-base">
            Start your crypto trading journey with CryptoOrchestrator
          </CardDescription>
        </CardHeader>
        <form onSubmit={handleSubmit}>
          <CardContent className="space-y-4">
            {error && (
              <Alert variant="destructive" className="animate-fade-in">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
            
            <div className="space-y-2">
              <Label htmlFor="fullName">Full Name</Label>
              <Input
                id="fullName"
                name="fullName"
                type="text"
                placeholder="John Doe"
                value={formData.fullName}
                onChange={(e) => handleChange("fullName", e.target.value)}
                disabled={isLoading}
                autoComplete="name"
                className={validationErrors.fullName ? "border-destructive" : ""}
                aria-invalid={!!validationErrors.fullName}
                aria-describedby={validationErrors.fullName ? "fullName-error" : undefined}
              />
              {validationErrors.fullName && (
                <p id="fullName-error" className="text-sm text-destructive animate-fade-in">
                  {validationErrors.fullName}
                </p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                name="email"
                type="email"
                placeholder="you@example.com"
                value={formData.email}
                onChange={(e) => handleChange("email", e.target.value)}
                required
                disabled={isLoading}
                autoComplete="email"
                className={validationErrors.email ? "border-destructive" : ""}
                aria-invalid={!!validationErrors.email}
                aria-describedby={validationErrors.email ? "email-error" : undefined}
              />
              {validationErrors.email && (
                <p id="email-error" className="text-sm text-destructive animate-fade-in">
                  {validationErrors.email}
                </p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="username">Username</Label>
              <Input
                id="username"
                name="username"
                type="text"
                placeholder="johndoe"
                value={formData.username}
                onChange={(e) => handleChange("username", e.target.value.toLowerCase())}
                required
                disabled={isLoading}
                autoComplete="username"
                className={validationErrors.username ? "border-destructive" : ""}
                aria-invalid={!!validationErrors.username}
                aria-describedby={validationErrors.username ? "username-error" : undefined}
              />
              {validationErrors.username && (
                <p id="username-error" className="text-sm text-destructive animate-fade-in">
                  {validationErrors.username}
                </p>
              )}
              <p className="text-xs text-muted-foreground">
                Only letters, numbers, underscores, and hyphens allowed
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <div className="relative">
                <Input
                  id="password"
                  name="password"
                  type={showPassword ? "text" : "password"}
                  placeholder="••••••••"
                  value={formData.password}
                  onChange={(e) => handleChange("password", e.target.value)}
                  required
                  disabled={isLoading}
                  autoComplete="new-password"
                  className={validationErrors.password ? "border-destructive pr-10" : "pr-10"}
                  aria-invalid={!!validationErrors.password}
                  aria-describedby={validationErrors.password ? "password-error" : undefined}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                  aria-label={showPassword ? "Hide password" : "Show password"}
                  tabIndex={-1}
                >
                  {showPassword ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </button>
              </div>
              {formData.password && (
                <PasswordStrengthIndicator password={formData.password} />
              )}
              {validationErrors.password && (
                <p id="password-error" className="text-sm text-destructive animate-fade-in">
                  {validationErrors.password}
                </p>
              )}
              <p className="text-xs text-muted-foreground">
                Must be at least 12 characters with uppercase, lowercase, numbers, and special characters
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="confirmPassword">Confirm Password</Label>
              <div className="relative">
                <Input
                  id="confirmPassword"
                  name="confirmPassword"
                  type={showConfirmPassword ? "text" : "password"}
                  placeholder="••••••••"
                  value={formData.confirmPassword}
                  onChange={(e) => handleChange("confirmPassword", e.target.value)}
                  required
                  disabled={isLoading}
                  autoComplete="new-password"
                  className={validationErrors.confirmPassword ? "border-destructive pr-10" : "pr-10"}
                  aria-invalid={!!validationErrors.confirmPassword}
                  aria-describedby={validationErrors.confirmPassword ? "confirmPassword-error" : undefined}
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                  aria-label={showConfirmPassword ? "Hide password" : "Show password"}
                  tabIndex={-1}
                >
                  {showConfirmPassword ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </button>
              </div>
              {validationErrors.confirmPassword && (
                <p id="confirmPassword-error" className="text-sm text-destructive animate-fade-in">
                  {validationErrors.confirmPassword}
                </p>
              )}
            </div>

            <div className="space-y-2">
              <div className="flex items-start space-x-2">
                <input
                  type="checkbox"
                  id="acceptTerms"
                  name="acceptTerms"
                  aria-label="Accept terms and conditions"
                  checked={formData.acceptTerms}
                  onChange={(e) => handleChange("acceptTerms", e.target.checked)}
                  className="h-4 w-4 mt-1 rounded border-gray-300 text-primary focus:ring-primary"
                  disabled={isLoading}
                />
                <Label htmlFor="acceptTerms" className="text-sm font-normal leading-tight cursor-pointer">
                  I agree to the{" "}
                  <Link href="/terms" className="text-primary hover:underline">
                    Terms of Service
                  </Link>{" "}
                  and{" "}
                  <Link href="/privacy" className="text-primary hover:underline">
                    Privacy Policy
                  </Link>
                </Label>
              </div>
              {validationErrors.acceptTerms && (
                <p className="text-sm text-destructive animate-fade-in">
                  {validationErrors.acceptTerms}
                </p>
              )}
            </div>
          </CardContent>
          <CardFooter className="flex flex-col space-y-4">
            <Button
              type="submit"
              className="w-full"
              disabled={!isFormValid()}
            >
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Creating account...
                </>
              ) : (
                <>
                  <UserPlus className="mr-2 h-4 w-4" />
                  Create account
                </>
              )}
            </Button>
            <div className="text-center text-sm text-muted-foreground">
              Already have an account?{" "}
              <Link href="/login" className="text-primary hover:underline font-medium">
                Sign in
              </Link>
            </div>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
}
