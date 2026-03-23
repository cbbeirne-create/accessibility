# Auditly - Website Accessibility Scanner PRD

## Product Overview
Auditly is a full-stack SaaS application for scanning website accessibility. It helps teams identify and fix accessibility issues to ensure WCAG 2.1 compliance.

## Tech Stack
- **Frontend**: React, Tailwind CSS, lucide-react icons
- **Backend**: FastAPI, Motor (async MongoDB driver)
- **Database**: MongoDB
- **Authentication**: JWT (bcrypt for password hashing)
- **Payments**: Stripe (placeholder keys - ready for production keys)
- **Accessibility Scanning**: Playwright + axe-core

## Core Features (Implemented ✅)

### 1. User Authentication
- ✅ User signup with email/password
- ✅ User login with JWT tokens
- ✅ Protected routes requiring authentication
- ✅ Auth context for state management
- ✅ Forgot Password flow (email reset link)
- ✅ Reset Password page with token validation

### 2. Subscription & Paywall System
- ✅ Free plan: 2 scans/month
- ✅ Pro plan: Unlimited scans, PDF export (requires Stripe keys)
- ✅ Scan limit enforcement on backend
- ✅ User profile showing plan and remaining scans
- ✅ Pricing page with plan comparison
- ✅ Stripe checkout integration (needs production keys)

### 3. Accessibility Scanning
- ✅ Playwright headless browser automation
- ✅ axe-core accessibility testing engine
- ✅ Full page screenshot capture
- ✅ Visual evidence with highlighted issues
- ✅ WCAG reference tagging
- ✅ Remediation guidance ("How to fix it")

### 4. Reports & Export
- ✅ PDF report generation
- ✅ JSON export for developers
- ✅ Screenshot export
- ✅ Detailed issue breakdown with selectors

### 5. Premium Enterprise UI
- ✅ Dark theme (slate-950 background)
- ✅ Emerald/teal gradient accents
- ✅ Responsive design
- ✅ Landing page for non-authenticated users
- ✅ Dashboard with stats cards
- ✅ Clean login/signup forms
- ✅ Pricing page with feature comparison

## API Endpoints

### Authentication
- `POST /api/auth/signup` - Create new account
- `POST /api/auth/login` - Login and get JWT
- `GET /api/auth/me` - Get current user profile
- `POST /api/auth/forgot-password` - Request password reset email
- `GET /api/auth/verify-reset-token` - Validate reset token
- `POST /api/auth/reset-password` - Set new password with token

### Scans (Protected)
- `GET /api/scans` - List user's scans
- `POST /api/scans` - Create new scan
- `GET /api/scans/{id}` - Get scan details
- `GET /api/scans/{id}/export/pdf` - Export PDF report
- `GET /api/scans/{id}/export/json` - Export JSON data
- `GET /api/scans/{id}/screenshot` - Get screenshot

### Subscription
- `POST /api/subscription/create-checkout-session` - Start Stripe checkout
- `POST /api/subscription/webhook` - Stripe webhook handler

### Health
- `GET /api/health` - System health check

## Database Schema

### Users Collection
```json
{
  "id": "uuid",
  "email": "string",
  "full_name": "string",
  "hashed_password": "string",
  "plan": "free|pro",
  "subscription_status": "active|inactive|canceled",
  "stripe_customer_id": "string|null",
  "stripe_subscription_id": "string|null",
  "scans_used_this_month": "number",
  "current_period_start": "datetime",
  "current_period_end": "datetime",
  "created_at": "datetime"
}
```

### Scans Collection
```json
{
  "id": "uuid",
  "url": "string",
  "status": "pending|completed|error",
  "score": "number|null",
  "issues": {
    "passed": [],
    "failed": [],
    "incomplete": []
  },
  "tool": "axe-core",
  "user_id": "string",
  "full_page_screenshot": "base64|null",
  "evidence_screenshots": {},
  "scan_metadata": {},
  "createdAt": "datetime"
}
```

## Test Credentials
- Email: `test3@auditly.com`
- Password: `testpass123`

## Environment Variables

### Backend (.env)
```
MONGO_URL=mongodb://localhost:27017
DB_NAME=test_database
SECRET_KEY=your-secret-key
FRONTEND_URL=https://...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRO_PRICE_ID=price_...
```

### Frontend (.env)
```
REACT_APP_BACKEND_URL=https://...
```

## Pending Tasks (Backlog)

### P0 - Critical
- [ ] Add production Stripe keys for live payments
- [ ] Monthly scan count reset (cron job or webhook)

### P1 - Important
- [ ] Add real SendGrid API key for email sending (currently mocked)
- [ ] Email verification on signup
- [ ] Update ScanResultsPage with premium dark theme styling

### P2 - Nice to Have
- [ ] Refactor monolithic App.js into /pages, /components, /contexts
- [ ] Refactor server.py into modular structure with APIRouter
- [ ] Scheduled recurring scans
- [ ] Team/organization accounts
- [ ] Analytics dashboard for scan trends

### P3 - Future
- [ ] External API integrations (WAVE, EqualWeb, AccessiBe)
- [ ] Webhook notifications for scan completion
- [ ] Comparison reports between scans
- [ ] White-label reports

## Known Limitations
1. Stripe integration uses placeholder keys - checkout returns 503 error
2. SendGrid email integration uses placeholder keys - reset links logged to backend logs instead of being emailed
3. External scanning APIs (WAVE, EqualWeb, AccessiBe) require user API keys
4. PDF export requires Pro plan (paywall enforced)

## Testing Status
- ✅ Backend: 95% pass rate (18/19 tests)
- ✅ Frontend: 100% critical flows working
- ✅ E2E: Auth flow, scan creation, results display all verified
- ✅ ScanResultsPage: Updated with dark/emerald Enterprise theme
- ✅ PDF Export Template: Updated with Auditly branding
- ✅ Accessibility Audit: WCAG 2.1 AA compliant

## Accessibility Audit Fixes Applied (March 2026)
1. **Focus Indicators**: Visible emerald focus rings on all interactive elements (WCAG 2.4.7)
2. **Skip Link**: Added "Skip to main content" link for keyboard users (WCAG 2.4.1)
3. **Color Contrast**: Improved text contrast - slate-200/300 for labels, emerald-300 for links (4.5:1+ ratio)
4. **ARIA Labels**: All icons have aria-hidden="true", buttons have descriptive aria-labels
5. **Semantic Structure**: Proper heading hierarchy (H1 → H2 → H3) throughout
6. **Form Accessibility**: Labels properly associated with inputs via htmlFor/id, required indicators
7. **Keyboard Navigation**: Details/summary elements are keyboard-accessible (Enter/Space to toggle)
8. **Live Regions**: Error messages use role="alert" with aria-live="polite"
9. **Landmarks**: Main content wrapped in <main> with role="main"

## PDF Export Accessibility (WCAG-Compliant Tagged PDF)
1. **Document Metadata**: Title="Auditly Accessibility Report", Author, Subject, Keywords
2. **Heading Tags**: Proper H1 (title), H2 (sections), H3 (issues) hierarchy
3. **Table Headers**: Explicit header rows with styled differentiation
4. **Alt Text for Visuals**: Screenshot includes descriptive figure caption
5. **Reading Order**: Logical flow - Score → Details → Summary → Issues → Evidence
6. **High Contrast**: Dark text on light backgrounds, color-coded status indicators
7. **HTML Escaping**: All dynamic content escaped to prevent XML parsing errors

## Last Updated
- Date: March 23, 2026
- Session: Completed Forgot Password flow (frontend routes + backend integration)

## Changelog
### March 23, 2026 - Password Reset Feature
- Added `/forgot-password` and `/reset-password` routes to React Router
- Integrated ForgotPasswordPage and ResetPasswordPage components
- Verified "Forgot your password?" link on login page
- E2E tested full password reset flow
- Test report: `/app/test_reports/iteration_2.json` (100% pass rate)
