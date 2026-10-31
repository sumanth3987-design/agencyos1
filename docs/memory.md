# Project Memory & Context Baseline — AgencyOS

## 1. Project Profile
- **Repository:** `sumanth3987-design/agencyos1`
- **Target Location:** India (`Asia/Kolkata` IST timezone)
- **Primary Business:** Agency operating system running founder's agency first (Customer Zero) -> B2B SaaS for Indian agencies.
- **Current Baseline:** Saturday, October 31, 2026.

## 2. Verified Technical State
- Application Factory Pattern (`create_app`) boots cleanly in `run.py` (dev) and `app.py` (prod).
- SQLite database (`instance/agencyos.db`) successfully migrated with 7 fund-flow columns:
  - `professional_profile`: `upi_id`, `bank_account_number`, `bank_ifsc`, `pan_number`
  - `invoice`: `payout_status`, `payout_utr`, `payout_paid_at`
- Public blueprint (`app/routes/public.py`) registered and verified:
  - `/privacy`, `/terms`, `/refund-policy`, `/contact` return HTTP 200.
  - `/api/free-audit` handles POST requests with flash notification.
- All test suites (`smoke`, `auth`, `csrf`, `project_workflow`, `payments`) pass.