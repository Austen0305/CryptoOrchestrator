# Accessibility Checklist

Quick reference checklist for ensuring WCAG 2.1 AA compliance.

## Perceivable

### Text Alternatives
- [ ] All images have meaningful alt text
- [ ] Decorative images have empty alt text (`alt=""`)
- [ ] Icons have aria-labels
- [ ] Charts/graphs have text descriptions

### Time-based Media
- [ ] Videos have captions
- [ ] Audio has transcripts
- [ ] Auto-playing media can be paused

### Adaptable
- [ ] Content works without color
- [ ] Text can be resized to 200%
- [ ] Layout adapts to text size changes

### Distinguishable
- [ ] Text contrast ratio ≥ 4.5:1 (normal text)
- [ ] Text contrast ratio ≥ 3:1 (large text)
- [ ] Focus indicators are visible
- [ ] No content flashes >3 times/second

## Operable

### Keyboard Accessible
- [ ] All functionality works with keyboard
- [ ] Tab order is logical
- [ ] No keyboard traps
- [ ] Focus indicators are visible
- [ ] Keyboard shortcuts are documented

### Enough Time
- [ ] Time limits can be extended
- [ ] Auto-updating content can be paused
- [ ] Moving content can be stopped

### Seizures
- [ ] No flashing content
- [ ] Animations respect prefers-reduced-motion

### Navigable
- [ ] Pages have descriptive titles
- [ ] Headings are used properly
- [ ] Multiple navigation methods
- [ ] Skip links provided
- [ ] Focus order is logical

## Understandable

### Readable
- [ ] Language is identified (`lang` attribute)
- [ ] Unusual words are defined
- [ ] Abbreviations are explained

### Predictable
- [ ] Navigation is consistent
- [ ] Components work consistently
- [ ] Context changes are predictable

### Input Assistance
- [ ] Errors are identified clearly
- [ ] Labels are provided for all inputs
- [ ] Error suggestions are provided
- [ ] Required fields are marked

## Robust

### Compatible
- [ ] Valid HTML
- [ ] ARIA attributes used correctly
- [ ] Name, role, value are programmatically determinable
- [ ] Works with assistive technologies

---

## Component-Specific Checklist

### Buttons
- [ ] Accessible name (text or aria-label)
- [ ] Keyboard accessible
- [ ] Focus indicator
- [ ] Disabled state communicated

### Forms
- [ ] All inputs have labels
- [ ] Required fields marked
- [ ] Error messages associated
- [ ] Validation is clear

### Modals
- [ ] Focus trapped
- [ ] Focus returns on close
- [ ] Escape key closes
- [ ] Has aria-label

### Navigation
- [ ] Skip links
- [ ] Landmarks used
- [ ] Current page indicated
- [ ] Keyboard accessible

---

## Testing Checklist

### Automated
- [ ] axe-core tests pass
- [ ] Lighthouse accessibility score ≥ 90
- [ ] WAVE extension shows no errors

### Manual
- [ ] Keyboard navigation tested
- [ ] Screen reader tested (NVDA/VoiceOver)
- [ ] Color contrast verified
- [ ] Text resize tested

---

**Last Updated**: December 12, 2025
