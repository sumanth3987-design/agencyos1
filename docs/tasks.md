# Master Implementation Tasks — AgencyOS

## Phase 0: Baseline Audit & Safety Verification (DONE)
- [x] 0.1 Audit entry points (`app.py`, `run.py`).
- [x] 0.2 Audit security configuration (`app/config.py`).
- [x] 0.3 Inspect existing database schema (`app/__init__.py`).
- [x] 0.4 Initialize 10-file documentation suite and `DECISIONS.md`.

## Phase 1: Visual Overhaul & Legal Foundation (IN PROGRESS)
- [x] 1.1 Create `app/routes/public.py` and register `public_bp`.
- [x] 1.2 Create `templates/legal/{privacy,terms,refund,contact}.html`.
- [x] 1.3 Add flash message handler for `/api/free-audit` on `templates/index.html`.
- [x] 1.4 Execute `apply_fund_flow_columns.py` to add banking and payout tracking columns.
- [x] 1.5 Redesign `templates/index.html` with high-conversion neuromarketing triggers.
- [x] 1.6 Redesign `templates/admin_dashboard.html` with Studio Dark Corbel aesthetic.
- [x] 1.7 Redesign `templates/dashboard.html` (Client Portal) with dark KPI tiles.
- [ ] 1.8 Redesign `templates/admin_base.html` (Admin core shell).
- [ ] 1.9 Redesign `templates/customer_project_details.html` (Deliverable review & revision gate).
- [ ] 1.10 Redesign `templates/payment.html` (Razorpay dark checkout).
- [ ] 1.11 Redesign `templates/professional_dashboard.html` and workspace.
- [ ] 1.12 Redesign `templates/login.html` and `templates/register.html`.

## Phase 2: Delivery & Revision Gate
- [ ] 2.1 Add `revision_count` check in `app/routes/customer.py`.
- [ ] 2.2 Wire 2-revision lockout logic with 1-click paid scope add-on modal.

## Phase 3: SEO Retainer Engine
- [ ] 3.1 Build 30-day recurring sprint checklist view.
- [ ] 3.2 Implement monthly cycle rollover logic.

## Phase 4: GST Invoicing & Payments
- [ ] 4.1 Implement SAC 998311 tax calculation service.
- [ ] 4.2 Connect Razorpay order generation and webhook listener in `app/routes/payments.py`.
- [ ] 4.3 Build talent payout disbursement recording interface in Admin portal.

## Phase 5: Google Gemini Copilot
- [ ] 5.1 Create `app/services/ai_service.py` wrapping the Gemini API.
- [ ] 5.2 Build backend routes for proposal drafting and monthly SEO executive summaries.