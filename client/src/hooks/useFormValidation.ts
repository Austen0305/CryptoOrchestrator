/**
 * Form Validation Hook
 * Provides real-time validation feedback with debouncing
 */

import { useState, useCallback, useEffect, useRef } from "react";
import { debounce } from "@/utils/performance";

interface ValidationRule<T = unknown> {
  validate: (value: T) => boolean | string;
  message?: string;
}

interface UseFormValidationOptions {
  debounceMs?: number;
  validateOnChange?: boolean;
  validateOnBlur?: boolean;
}

interface FieldValidation {
  error?: string;
  isValid: boolean;
  isDirty: boolean;
  isTouched: boolean;
}

export function useFormValidation<T extends Record<string, unknown>>(
  initialValues: T,
  rules: Partial<Record<keyof T, ValidationRule[]>>,
  options: UseFormValidationOptions = {}
) {
  const {
    debounceMs = 300,
    validateOnChange = true,
    validateOnBlur = true,
  } = options;

  const [values, setValues] = useState<T>(initialValues);
  const [errors, setErrors] = useState<Partial<Record<keyof T, string>>>({});
  const [touched, setTouched] = useState<Partial<Record<keyof T, boolean>>>({});
  const [dirty, setDirty] = useState<Partial<Record<keyof T, boolean>>>({});

  // Debounced validation function
  const validateField = useCallback(
    debounce((...args: unknown[]) => {
      const fieldName = args[0] as keyof T;
      const value = args[1];
      const fieldRules = rules[fieldName];
      if (!fieldRules || fieldRules.length === 0) return;

      for (const rule of fieldRules) {
        const result = rule.validate(value);
        if (result !== true) {
          const errorMessage =
            typeof result === "string" ? result : rule.message || "Invalid value";
          setErrors((prev) => ({ ...prev, [fieldName]: errorMessage }));
          return;
        }
      }

      // No errors found
      setErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors[fieldName];
        return newErrors;
      });
    }, debounceMs),
    [rules, debounceMs]
  );

  // Validate all fields
  const validateAll = useCallback(() => {
    const newErrors: Partial<Record<keyof T, string>> = {};

    for (const fieldName in rules) {
      const fieldRules = rules[fieldName];
      if (!fieldRules || fieldRules.length === 0) continue;

      const value = values[fieldName];
      for (const rule of fieldRules) {
        const result = rule.validate(value);
        if (result !== true) {
          newErrors[fieldName] =
            typeof result === "string" ? result : rule.message || "Invalid value";
          break;
        }
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }, [values, rules]);

  // Handle field change
  const handleChange = useCallback(
    (fieldName: keyof T) => (value: unknown) => {
      setValues((prev) => ({ ...prev, [fieldName]: value }));
      setDirty((prev) => ({ ...prev, [fieldName]: true }));

      if (validateOnChange) {
        validateField(fieldName, value);
      }
    },
    [validateOnChange, validateField]
  );

  // Handle field blur
  const handleBlur = useCallback(
    (fieldName: keyof T) => () => {
      setTouched((prev) => ({ ...prev, [fieldName]: true }));

      if (validateOnBlur) {
        validateField(fieldName, values[fieldName]);
      }
    },
    [validateOnBlur, validateField, values]
  );

  // Get field validation state
  const getFieldState = useCallback(
    (fieldName: keyof T): FieldValidation => {
      return {
        error: errors[fieldName],
        isValid: !errors[fieldName],
        isDirty: dirty[fieldName] || false,
        isTouched: touched[fieldName] || false,
      };
    },
    [errors, dirty, touched]
  );

  // Reset form
  const reset = useCallback(() => {
    setValues(initialValues);
    setErrors({});
    setTouched({});
    setDirty({});
  }, [initialValues]);

  // Check if form is valid
  const isValid = Object.keys(errors).length === 0;

  return {
    values,
    errors,
    touched,
    dirty,
    isValid,
    handleChange,
    handleBlur,
    getFieldState,
    validateAll,
    reset,
    setValues,
  };
}

/**
 * Common validation rules
 */
export const validationRules = {
  required: (message = "This field is required"): ValidationRule => ({
    validate: (value) => {
      if (value === null || value === undefined || value === "") {
        return message;
      }
      if (typeof value === "string" && value.trim() === "") {
        return message;
      }
      return true;
    },
    message,
  }),

  minLength: (min: number, message?: string): ValidationRule => ({
    validate: (value) => {
      if (typeof value === "string" && value.length < min) {
        return message || `Must be at least ${min} characters`;
      }
      return true;
    },
    message: message || `Must be at least ${min} characters`,
  }),

  maxLength: (max: number, message?: string): ValidationRule => ({
    validate: (value) => {
      if (typeof value === "string" && value.length > max) {
        return message || `Must be no more than ${max} characters`;
      }
      return true;
    },
    message: message || `Must be no more than ${max} characters`,
  }),

  email: (message = "Invalid email address"): ValidationRule => ({
    validate: (value) => {
      if (typeof value !== "string") return true;
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      return emailRegex.test(value) || message;
    },
    message,
  }),

  number: (message = "Must be a number"): ValidationRule => ({
    validate: (value) => {
      if (value === null || value === undefined || value === "") return true;
      return !isNaN(Number(value)) || message;
    },
    message,
  }),

  min: (min: number, message?: string): ValidationRule => ({
    validate: (value) => {
      const num = Number(value);
      if (isNaN(num)) return true;
      return num >= min || message || `Must be at least ${min}`;
    },
    message: message || `Must be at least ${min}`,
  }),

  max: (max: number, message?: string): ValidationRule => ({
    validate: (value) => {
      const num = Number(value);
      if (isNaN(num)) return true;
      return num <= max || message || `Must be no more than ${max}`;
    },
    message: message || `Must be no more than ${max}`,
  }),

  pattern: (pattern: RegExp, message = "Invalid format"): ValidationRule => ({
    validate: (value) => {
      if (typeof value !== "string") return true;
      return pattern.test(value) || message;
    },
    message,
  }),
};
