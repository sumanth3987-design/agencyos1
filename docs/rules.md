---

### 3. `docs/rules.md`

```markdown
# Engineering & Operating Rules — AgencyOS

## 1. Solo-Developer Guardrails
1. **Rule of Simplicity:** Always use server-rendered Flask + Jinja templates styled with Tailwind utility classes. Do NOT introduce decoupled SPA build pipelines (React/Vite) into core operations.
2. **Unified Shell Principle:** All role-specific views must share the same Studio Dark design tokens (`zinc-950`, Plus Jakarta Sans, Lucide icons).
3. **Additive Schema Migrations Only:** Never drop tables or execute unversioned `ALTER TABLE` scripts. Always run non-destructive additive migrations like `apply_fund_flow_columns.py`.

## 2. Security & Secrets Management
1. **Zero Secret Leakage:** `GEMINI_API_KEY`, `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`, and `SECRET_KEY` must be loaded exclusively via environment variables. Client bundles must never access API keys.
2. **Production Validation:** If `FLASK_ENV=production`, `config.py` strictly raises `InsecureSecretKeyError` or `InsecureRazorpayCredentialsError` if placeholder keys are detected.
3. **Session Hardening:** All session cookies must enforce `HttpOnly=True`, `SameSite='Lax'`, and `Secure=True` in production.

## 3. Compliance & Legal Rules (India)
1. **Digital Personal Data Protection Act (2023):** Only collect necessary client data (Name, Email, Phone, GSTIN). Provide a visible Grievance Officer contact.
2. **Consumer Protection Act:** No fabricated reviews, fake customer numbers, or unsupported marketing guarantees.
3. **Razorpay KYC Requirement:** All deployments must maintain live, accessible `/privacy`, `/terms`, `/refund-policy`, and `/contact` endpoints.

## 4. UI/UX Rules
1. **Zero Horizontal Overflow:** All views must maintain `overflow-x: hidden` and render cleanly on mobile viewport sizes (375px+).
2. **Tabular Figures:** All Indian Rupee figures must use monospace or tabular numerals (`font-mono`) to prevent visual layout shifts.
3. **No Inline CSS with Curly Brackets:** Never write inline Jinja expressions inside `style=""` (e.g., `style="width: {{ x }}%"`). Use `data-progress` attributes and script-driven widths to avoid IDE CSS parser errors.

### 4. Tailwind CSS v4 & Modal Engineering Rules
- **Canonical Gradients:** Never use legacy `bg-gradient-to-*`. Always write `bg-linear-to-tr`, `bg-linear-to-r`, etc.
- **Modal Display Purity:** Never combine conflicting `hidden` and `fixed` display classes directly in modal shells. Use `fixed inset-0 z-50 flex items-center justify-center` managed via clean style toggling (`display: none` / `display: flex`) to avoid layout jumps.