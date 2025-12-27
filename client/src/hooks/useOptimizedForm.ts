/**
 * Optimized Form Hook
 * Enhanced form handling with validation and performance optimizations
 */

import { useState, useCallback, useMemo } from 'react';
import { validateEmail, validateAmount, validateEthereumAddress, sanitizeInput } from '@/utils/validation';
import { showErrorToast } from '@/utils/error-handling';

interface FormField<T> {
  value: T;
  error?: string;
  touched: boolean;
}

interface UseOptimizedFormOptions<T> {
  initialValues: T;
  validate?: (values: T) => Partial<Record<keyof T, string>>;
  onSubmit: (values: T) => Promise<void> | void;
}

export function useOptimizedForm<T extends Record<string, unknown>>({
  initialValues,
  validate,
  onSubmit,
}: UseOptimizedFormOptions<T>) {
  const [values, setValues] = useState<T>(initialValues);
  const [errors, setErrors] = useState<Partial<Record<keyof T, string>>>({});
  const [touched, setTouched] = useState<Partial<Record<keyof T, boolean>>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Memoize validation
  const validateForm = useCallback(
    (formValues: T): boolean => {
      const validationErrors = validate ? validate(formValues) : {};
      setErrors(validationErrors);
      return Object.keys(validationErrors).length === 0;
    },
    [validate]
  );

  // Handle field change
  const handleChange = useCallback(
    (name: keyof T) => (value: unknown) => {
      setValues((prev) => ({ ...prev, [name]: value }));
      
      // Clear error when user starts typing
      if (errors[name]) {
        setErrors((prev) => {
          const newErrors = { ...prev };
          delete newErrors[name];
          return newErrors;
        });
      }
    },
    [errors]
  );

  // Handle field blur
  const handleBlur = useCallback((name: keyof T) => {
    setTouched((prev) => ({ ...prev, [name]: true } as any));
    
    // Validate field on blur
    const fieldErrors = validate ? validate(values) : ({} as Partial<Record<keyof T, string>>);
    if (fieldErrors[name]) {
      setErrors((prev) => ({ ...prev, [name]: fieldErrors[name] } as any));
    }
  }, [values, validate]);

  // Handle form submit
  const handleSubmit = useCallback(
    async (e?: React.FormEvent) => {
      e?.preventDefault();
      
      // Mark all fields as touched
      const allTouched = Object.keys(values).reduce((acc, key) => {
        acc[key as keyof T] = true;
        return acc;
      }, {} as Partial<Record<keyof T, boolean>>);
      setTouched(allTouched);

      // Validate form
      if (!validateForm(values)) {
        return;
      }

      setIsSubmitting(true);
      try {
        await onSubmit(values);
      } catch (error) {
        showErrorToast(error, 'Form submission');
      } finally {
        setIsSubmitting(false);
      }
    },
    [values, validateForm, onSubmit]
  );

  // Reset form
  const reset = useCallback(() => {
    setValues(initialValues);
    setErrors({});
    setTouched({});
  }, [initialValues]);

  // Get field props
  const getFieldProps = useCallback(
    (name: keyof T) => ({
      value: values[name],
      error: touched[name] ? errors[name] : undefined,
      onChange: handleChange(name),
      onBlur: () => handleBlur(name),
    }),
    [values, errors, touched, handleChange, handleBlur]
  );

  const isValid = useMemo(() => Object.keys(errors).length === 0, [errors]);

  return {
    values,
    errors,
    touched,
    isSubmitting,
    isValid,
    handleChange,
    handleBlur,
    handleSubmit,
    reset,
    getFieldProps,
    setValues,
  };
}

