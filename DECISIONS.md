# Architecture Decision Log — AgencyOS

## Purpose
This document records all confirmed architectural, technical, security, data, and business-logic decisions for AgencyOS (`sumanth3987-design/agencyos1`). 

It ensures future developers and AI agents preserve architectural intent instead of guessing or undoing established constraints.

---

## Rules for Future AI Agents
1. Read this file before making architecture-level changes.
2. Treat `CONFIRMED` decisions as intentional, non-negotiable constraints.
3. Do NOT contradict a confirmed decision without explicit human authorization.
4. Do NOT replace existing server-side Jinja/Flask architectures with external SPA frameworks.
5. If a proposed change conflicts with an existing decision, report the conflict first.

---

## Decision Index

| ID | Decision Name | Status | Area |
| :--- | :--- | :--- | :--- |
| **DEC-001** | Primary Production Backend Runtime (Flask Monolith) | `CONFIRMED` | Architecture |
| **DEC-002** | React / Vite Codebase Role (Exported Prototype Reference) | `CONFIRMED` | Frontend |
| **DEC-003** | Authentication & Session Management (Flask-Login + CSRF) | `CONFIRMED` | Security |
| **DEC-004** | Development Database Engine (Local SQLite) | `CONFIRMED` | Database |
| **DEC-005** | Safe Additive Schema Evolution (`apply_fund_flow_columns.py`) | `CONFIRMED` | Database |
| **DEC-006** | Primary Payment Gateway Rail (Razorpay India) | `CONFIRMED` | Payments |
| **DEC-007** | Payment Verification & Idempotency Enforcement | `CONFIRMED` | Security / Payments |
| **DEC-008** | Google Gemini AI Confinement to Backend Routes | `CONFIRMED` | Security / AI |
| **DEC-009** | Go-To-Market & Business Model (Customer Zero Dogfooding) | `CONFIRMED` | Business Logic |
| **DEC-010** | Dual Core Service Delivery Engine (Milestones vs Retainers) | `CONFIRMED` | Business Logic |
| **DEC-011** | Portal Topology (Role-Gated Shared Monolith Views) | `CONFIRMED` | Architecture / UI |
| **DEC-012** | Multi-Tenancy Isolation Strategy (Row-Level `agency_id`) | `CONFIRMED` | Architecture / Database |
| **DEC-013** | Package Manager Standardization (NPM) | `CONFIRMED` | Infrastructure |
| **DEC-014** | Deliverable Scope Creep Limitation (2-Revision Cap) | `CONFIRMED` | Business Logic |
| **DEC-015** | UI Design System Language (Linear/Corbel Studio Dark) | `CONFIRMED` | UI / UX |
| **DEC-016** | Behavioral Economics & Conversion Architecture | `CONFIRMED` | Business Logic |
| **DEC-017** | Fund Flow & Talent Payout Architecture | `CONFIRMED` | Finance / Operations |
| **DEC-018** | Legal & DPDP Compliance Baseline (Razorpay KYC Ready) | `CONFIRMED` | Legal / Compliance |

---

## Detailed Decisions

### DEC-015 — UI Design System Language (Linear/Corbel Studio Dark)
* **Status:** `CONFIRMED`
* **Area:** UI / UX
* **Decision:** All views adopt an ultra-clean, minimal dark-mode aesthetic inspired by `shadcn/ui`, `Linear`, and `Corbel Supply Co.`: Base canvas `#09090b` (`zinc-950`), cards `#121215`, subtle borders `rgba(255,255,255,0.07)`, Plus Jakarta Sans typography, tabular figures for INR metrics, and Lucide icons.
* **Why:** Replaces clunky, generic light templates with an executive studio workspace that justifies high-ticket agency retainers (₹50k – ₹1.5L+).
* **Impact:** `templates/base.html`, `templates/admin_dashboard.html`, `templates/dashboard.html`.

### DEC-016 — Behavioral Economics & Conversion Architecture
* **Status:** `CONFIRMED`
* **Area:** Business Logic / UI
* **Decision:** The platform natively implements 10 behavioral triggers: Reciprocity (AI free audit hook), Authority (dark UI + SAC 998311 compliance), Anchoring (₹1.25L enterprise anchor), Decoy Pricing (SEO retainers), Paradox of Choice (max 3 tiers), Scarcity (capacity slots indicator), Urgency (72-hour price guarantee), Goal Gradient (25% starter progress bar), Loss Aversion (ranking protection warnings), and Social Proof (client metrics counters).
* **Why:** Systematically increases advance invoice collection rates and stops client churn for a solo agency founder.

### DEC-017 — Fund Flow & Talent Payout Architecture
* **Status:** `CONFIRMED`
* **Area:** Finance / Operations
* **Decision:** Inbound client funds are collected 100% by the agency via Razorpay into the agency's primary account. Outbound talent payouts are released ONLY after client deliverable approval. Payouts are tracked via `payout_status` (`Pending Approval` -> `Ready to Pay` -> `Paid`) and reconciled with a bank transaction reference (`payout_utr`).
* **Why:** Guarantees cash flow control, prevents freelancer abandonment, and eliminates dispute liability.
* **Evidence:** `apply_fund_flow_columns.py`, `app/__init__.py`.

### DEC-018 — Legal & DPDP Compliance Baseline (Razorpay KYC Ready)
* **Status:** `CONFIRMED`
* **Area:** Legal / Compliance
* **Decision:** The application maintains 4 dedicated, static legal endpoints: `/privacy` (India DPDP Act 2023 compliant), `/terms` (milestone gates & 2-revision policy), `/refund-policy` (advance deposit non-refundable terms), and `/contact` (registered Indian office & grievance contact).
* **Why:** Mandatory requirement for Razorpay merchant activation and Indian statutory compliance.
* **Evidence:** `app/routes/public.py`, `templates/legal/`.