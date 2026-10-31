# UI/UX & Design Specification — AgencyOS

## 1. Design Language & Tokens
Inspired by `Linear`, `shadcn/ui`, `Kokonut UI`, and `Corbel Supply Co.`:
- **Base Canvas:** `#09090b` (`zinc-950`)
- **Card Surface:** `#121215` (`zinc-900/60` with subtle border `rgba(255, 255, 255, 0.07)`)
- **Card Hover:** `rgba(255, 255, 255, 0.16)` border with `translateY(-2px)` elevation
- **Typography:** **Plus Jakarta Sans** for headings, **JetBrains Mono** for figures and dates
- **Accents:**
  - Success / Approved: `#10b981` (Emerald)
  - Review / Warning: `#f59e0b` (Amber)
  - Payment Due / Danger: `#f43f5e` (Rose)
  - Primary CTA / Sprints: `#6366f1` (Indigo) / `#ffffff` (White button on dark canvas)

## 2. Core Layout Primitives
1. **Floating Segmented Pill Bar:** Compact, rounded navigation header (`Overview`, `Milestones`, `Analytics`, `Invoices`).
2. **KPI Metric Tiles:** Ambient hover glow, Lucide trending icon, live percentage comparison chip, and micro progress bar.
3. **Pipeline Cards:** 7-stage visual tracker with animated percentage track fills.
4. **Approval Gate Card:** High-contrast green `[Approve Deliverable]` button alongside amber `[Request Revision]` button displaying remaining complimentary revisions.

## 3. Accessibility & Clean Code Standards
- Zero inline CSS expressions containing Jinja curly brackets.
- Responsive mobile drawer with zero horizontal scroll overflow.
- High color contrast ratio meeting WCAG AA standards.