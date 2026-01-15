/**
 * Optimized Accordion Component
 * High-performance accordion with lazy loading
 */

import React, { useState, useCallback } from 'react';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from './ui/accordion';
import { cn } from '@/lib/utils';

interface AccordionSection {
  value: string;
  title: string;
  content: React.ReactNode;
  disabled?: boolean;
}

interface OptimizedAccordionProps {
  sections: AccordionSection[];
  type?: 'single' | 'multiple';
  defaultValue?: string | string[];
  className?: string;
  lazy?: boolean;
}

export function OptimizedAccordion({
  sections,
  type = 'single',
  defaultValue,
  className,
  lazy = true,
}: OptimizedAccordionProps) {
  const [openSections, setOpenSections] = useState<Set<string>>(
    new Set(Array.isArray(defaultValue) ? defaultValue : defaultValue ? [defaultValue] : [])
  );

  const handleValueChange = useCallback((value: string | string[]) => {
    if (type === 'single') {
      setOpenSections(new Set(typeof value === 'string' ? [value] : []));
    } else {
      setOpenSections(new Set(Array.isArray(value) ? value : []));
    }
  }, [type]);

  return (
    // @ts-ignore - Accordion type union is complex
    <Accordion
      type={type}
      defaultValue={defaultValue}
      onValueChange={handleValueChange}
      className={cn(className)}
    >
      {sections.map((section) => (
        <AccordionItem key={section.value} value={section.value} disabled={section.disabled}>
          <AccordionTrigger>{section.title}</AccordionTrigger>
          <AccordionContent>
            {lazy && !openSections.has(section.value) ? null : (section.content as any)}
          </AccordionContent>
        </AccordionItem>
      ))}
    </Accordion>
  );
}

