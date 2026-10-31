# Product Requirements Document (PRD) — AgencyOS

## 1. Executive Summary & Vision
AgencyOS is an integrated operating system built for boutique digital marketing, web design, and SEO agencies in India (2–15 team members). It operates under a "Customer Zero / Dogfooding" strategy: the founder runs their own agency on the platform first to validate workflows, cash flow, and client approvals before expanding into a multi-tenant B2B SaaS.

## 2. Market Fit (India-First Reality)
- **Indian Standard Time (IST):** All cron jobs, sprint rollovers, and invoice dates run on `Asia/Kolkata`.
- **Statutory Taxation:** Native SAC Code 998311 compliance with automatic CGST + SGST (intra-state) or IGST (inter-state) calculation.
- **Payment Rails:** Native UPI QR codes and Razorpay Orders integration with strict partial unique index idempotency.
- **WhatsApp Integration:** Zero-password magic links for instant smartphone review and deliverable sign-offs without client account creation friction.

## 3. Core Modules & Feature Specifications

### Module 1: Website Delivery Engine (Milestone-Gated)
- **3 Phased Gates:** 50% Advance Deposit -> 25% Wireframe/Design Sign-off -> 25% Production Deployment.
- **Sequential Unlocks:** Milestone 2 cannot start until Milestone 1 payment is verified via Razorpay webhook.
- **2-Revision Guarantee:** Client portal caps complimentary feedback at 2 revision rounds per milestone. A 1-click paid scope add-on button unlocks additional modifications.

### Module 2: SEO Retainer Engine (30-Day Cyclical Sprints)
- **4 Monthly Deliverable Tracks:** Technical Audit, On-Page Optimization, Content/Backlinks, and Performance Metrics.
- **Day 28 Review Trigger:** System auto-compiles monthly deliverables into an executive summary for client renewal.
- **Loss-Aversion Retention Alerts:** Warns clients of ranking drops before they pause their monthly retainer.

### Module 3: Indian Invoicing & Fund Flow Architecture
- **Inbound Collection:** 100% of client payments are collected upfront into the agency's primary bank account via Razorpay.
- **Outbound Talent Payout:** Funds for specialists are held in milestone escrow and marked `Ready to Pay` only after client deliverable approval.
- **Payout Tracking:** Payouts are recorded with `payout_status`, `payout_utr` (bank transaction reference), and `payout_paid_at`.

### Module 4: Corbel-Style Executive Workspace
- **Studio Dark Aesthetic:** High-density, minimal dark UI inspired by Linear and Corbel Supply Co. (`zinc-950` base, `#121215` cards).
- **Live KPI Tiles:** Real-time tracking of active revenue, leads captured, and sprint conversion rates.
- **Operational Pipeline:** 7-stage visual pipeline tracker (`Pending Assignment` to `Completed`).

### Module 5: Google Gemini AI Copilot (Backend-Confined)
- **SOW / Proposal Drafter:** Converts raw client notes into structured milestone packages and budgets.
- **SEO Monthly Report Drafter:** Automatically writes client-ready progress emails from completed sprint checklist items.

### Module 6: Statutory Compliance & Legal Suite
- **DPDP Act (2023):** Transparent privacy disclosures, minimal data collection, and Grievance Officer routing.
- **Merchant Activation Ready:** Dedicated, static legal endpoints (`/privacy`, `/terms`, `/refund-policy`, `/contact`) fulfilling Razorpay KYC mandates.