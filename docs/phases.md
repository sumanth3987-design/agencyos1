# Implementation Phases & Acceptance Criteria — AgencyOS

## Phase 0: Baseline Audit & Safety Verification (COMPLETED)
- [x] Record Git status and configuration baseline.
- [x] Safe database inspection: `instance/agencyos.db` verified.
- [x] Establish pytest test suite baseline.

## Phase 1: Studio Dark UI & Legal Foundation (CURRENT)
- [x] **Legal Suite:** `/privacy`, `/terms`, `/refund-policy`, `/contact` return HTTP 200.
- [x] **Lead Capture:** POST `/api/free-audit` stores inquiries and redirects with flash message.
- [x] **Public Landing Page:** High-conversion `templates/index.html` with social proof and pricing anchors.
- [x] **Admin Dashboard:** `templates/admin_dashboard.html` upgraded to Studio Dark Corbel aesthetic.
- [x] **Client Portal:** `templates/dashboard.html` upgraded to Studio Dark Corbel aesthetic.
- [ ] **Admin Base Shell:** Upgrade `templates/admin_base.html`.
- [ ] **Remaining Views:** Upgrade `admin_project_management.html`, `customer_project_details.html`, `payment.html`, and professional views.

## Phase 2: Delivery Engine & Scope Creep Lock
- **Acceptance Criteria:**
  - Client portal displays `[Approve Deliverable]` and `[Request Revision (X of 2 Left)]`.
  - When revision count reaches 2, button disables and reveals `[Request Paid Revision — ₹2,500]`.
  - Approved deliverable unlocks subsequent project milestone.

## Phase 3: SEO Retainer Engine
- **Acceptance Criteria:**
  - 30-day recurring sprint checklist tracks Technical, On-Page, Content, and Review tasks.
  - Day 28 auto-drafts monthly executive progress summary.

## Phase 4: GST Invoicing & Razorpay Webhooks
- **Acceptance Criteria:**
  - Invoices calculate CGST (9%) + SGST (9%) for intra-state or IGST (18%) for inter-state.
  - Razorpay webhook verifies HMAC signature and updates `Payment.status = 'Paid'`.
  - Admin dashboard records talent payout with transaction UTR number.

## Phase 5: Google Gemini Copilot
- **Acceptance Criteria:**
  - Route `/api/ai/proposal` outputs structured 3-milestone project scopes.
  - Route `/api/ai/seo-report` compiles completed tasks into client summaries.