# Auditly - Master System Architecture Summary

## Overview
Auditly is a full-stack SaaS website accessibility scanner that helps teams identify and fix WCAG 2.1 AA compliance issues. It features real browser-based scanning, user authentication, subscription billing, and accessible PDF report generation.

**Live Preview URL:** `https://remediation-lab.preview.emergentagent.com`

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 18, Tailwind CSS, lucide-react icons |
| Backend | FastAPI (Python 3.11), Gunicorn |
| Database | MongoDB (Motor async driver) |
| Authentication | JWT (python-jose, bcrypt) |
| Payments | Stripe Subscriptions |
| Email | SendGrid |
| Scanning | Playwright + axe-core |
| PDF Generation | ReportLab (Tagged PDF) |

---

## 1. Authentication System

### JWT-Based Auth Flow
```
User → POST /api/auth/signup → Create User + Stripe Customer → Return JWT
User → POST /api/auth/login → Verify Password → Return JWT
User → GET /api/auth/me (+ Bearer Token) → Return UserProfile
```

### Password Hashing
- Uses `bcrypt` directly (not passlib due to compatibility)
- Passwords truncated to 72 bytes (bcrypt limit)
- Location: `get_password_hash()`, `verify_password()` in server.py

### Token Configuration
```python
SECRET_KEY = os.environ.get('SECRET_KEY')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days
```

### User Model Fields
```python
class User(BaseModel):
    id: str                          # UUID
    email: EmailStr
    full_name: Optional[str]
    hashed_password: str
    plan: UserPlan                   # "free" | "pro"
    subscription_status: str         # "active" | "inactive" | "canceled"
    stripe_customer_id: Optional[str]
    stripe_subscription_id: Optional[str]
    scans_used_this_month: int       # Reset monthly on login
    current_period_start: datetime
    current_period_end: datetime
    password_reset_token: Optional[str]
    password_reset_expires: Optional[datetime]
    created_at: datetime
```

---

## 2. Password Reset Flow

### Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/forgot-password` | POST | Generate reset token, send email |
| `/api/auth/reset-password` | POST | Validate token, update password |
| `/api/auth/verify-reset-token` | GET | Check if token is valid (frontend) |

### Security Features
- Tokens: `secrets.token_urlsafe(32)` (cryptographically secure)
- Expiration: 1 hour
- One-time use: Token cleared after successful reset
- No email enumeration: Always returns success message

### Email Integration (SendGrid)
```python
# Environment variables
SENDGRID_API_KEY="your_key"
SENDER_EMAIL="noreply@auditly.com"
FRONTEND_URL="https://remediation-lab.preview.emergentagent.com"
```

**Dev Mode:** If SendGrid not configured, reset link logged to console for testing.

---

## 3. Stripe Subscription System

### Plans
| Plan | Price | Scans | PDF Export |
|------|-------|-------|------------|
| Free | $0 | 2/month | No |
| Pro | $29/month | Unlimited | Yes |

### Monthly Reset Logic
```python
async def check_and_reset_monthly_scan_count(user_id, current_period_start):
    # Called on login and /auth/me
    # Resets scans_used_this_month to 0 if new month detected
```

### Stripe Endpoints
| Endpoint | Description |
|----------|-------------|
| `/api/subscription/create-checkout-session` | Creates Stripe Checkout session |
| `/api/subscription/webhook` | Handles Stripe events |

### Graceful Degradation
- If Stripe keys are placeholders (`sk_test_your...`), customer creation is skipped
- Users can still sign up; Stripe features return 503

---

## 4. Accessibility Scanning Engine

### Architecture
```
POST /api/scans → Create scan record → Background task:
  1. Launch Playwright browser
  2. Navigate to URL
  3. Inject axe-core script
  4. Run accessibility audit
  5. Capture full-page screenshot
  6. Highlight failing elements
  7. Calculate score
  8. Store results in MongoDB
```

### Scan Model
```python
class ScanRequest(BaseModel):
    id: str
    url: HttpUrl
    status: ScanStatus      # "pending" | "completed" | "error"
    score: Optional[int]    # 0-100
    issues: {
        "passed": [...],
        "failed": [...],
        "incomplete": [...]
    }
    tool: str               # "axe-core"
    user_id: str
    full_page_screenshot: Optional[str]  # Base64
    createdAt: datetime
```

### Score Calculation
```python
score = 100 - (failed_count * 5)  # Each failure = -5 points
score = max(0, min(100, score))   # Clamp 0-100
```

### Remediation Guidance
`getRemediationGuidance(issue)` provides "How to fix it" suggestions based on issue ID (e.g., `color-contrast`, `image-alt`, `label`).

---

## 5. PDF Report Generation (WCAG-Compliant)

### Accessibility Features
1. **Document Metadata**: Title, Author, Subject, Keywords
2. **Heading Hierarchy**: H1 → H2 → H3
3. **Table Headers**: Explicit header rows styled differently
4. **Alt Text**: Figure captions describe screenshots
5. **Reading Order**: Logical flow (Score → Details → Issues)
6. **High Contrast**: Dark text on light backgrounds
7. **HTML Escaping**: `safe_text()` function prevents XML errors

### Export Endpoints
| Endpoint | Auth | Description |
|----------|------|-------------|
| `/api/scans/{id}/export/pdf` | Pro only | Download PDF report |
| `/api/scans/{id}/export/json` | All users | Download JSON data |
| `/api/scans/{id}/screenshot` | All users | View screenshot |

---

## 6. Frontend Architecture

### Theme: Dark/Emerald Enterprise
- Background: `slate-950` (#020617)
- Cards: `slate-900` (#0f172a)
- Accent: `emerald-400/500` (#34d399)
- Secondary: `teal-500` (#14b8a6)

### WCAG 2.1 AA Compliance
- Focus indicators: 2px emerald ring + 4px glow
- Skip link: "Skip to main content"
- Color contrast: 4.5:1+ ratio
- Form labels: Associated via htmlFor/id
- ARIA: Landmarks, live regions, describedby

### Key Components (all in App.js)
| Component | Route | Description |
|-----------|-------|-------------|
| `LoginPage` | `/login` | Email/password login |
| `SignupPage` | `/signup` | Registration form |
| `ForgotPasswordPage` | `/forgot-password` | Request reset email |
| `ResetPasswordPage` | `/reset-password?token=X` | Set new password |
| `Dashboard` | `/` | Landing (guest) or dashboard (auth) |
| `ScanPage` | `/scan` | Create new scan |
| `MyScansPage` | `/my-scans` | Scan history list |
| `ScanResultsPage` | `/scan-results/:id` | Detailed results |
| `PricingPage` | `/pricing` | Plan comparison |

### Auth Context
```javascript
const AuthContext = createContext();

// Provides: user, login(), signup(), logout(), isAuthenticated, loading
// Stores JWT in localStorage
// Auto-fetches /auth/me on mount
```

---

## 7. API Endpoints Summary

### Authentication
```
POST /api/auth/signup          → Create account, return JWT
POST /api/auth/login           → Authenticate, return JWT
GET  /api/auth/me              → Get user profile (requires auth)
POST /api/auth/forgot-password → Send reset email
POST /api/auth/reset-password  → Reset with token
GET  /api/auth/verify-reset-token?token=X → Check token validity
```

### Scans (require auth)
```
GET  /api/scans                → List user's scans
POST /api/scans                → Create new scan
GET  /api/scans/{id}           → Get scan details
GET  /api/scans/{id}/export/pdf   → Download PDF (Pro only)
GET  /api/scans/{id}/export/json  → Download JSON
GET  /api/scans/{id}/screenshot   → View screenshot
```

### Subscription
```
POST /api/subscription/create-checkout-session → Stripe checkout
POST /api/subscription/webhook                 → Stripe webhooks
```

### System
```
GET /api/health                → Health check (DB + Playwright)
GET /api/docs                  → Swagger UI
GET /api/external-apis/status  → External API configuration status
```

---

## 8. Environment Variables

### Backend (/app/backend/.env)
```bash
# Database
MONGO_URL="mongodb://localhost:27017"
DB_NAME="test_database"

# Auth
SECRET_KEY="your-super-secret-key"
FRONTEND_URL="https://remediation-lab.preview.emergentagent.com"

# Playwright
PLAYWRIGHT_BROWSERS_PATH="/pw-browsers"

# Stripe (placeholder - needs real keys)
STRIPE_PUBLISHABLE_KEY="pk_test_..."
STRIPE_SECRET_KEY="sk_test_..."
STRIPE_WEBHOOK_SECRET="whsec_..."
STRIPE_PRO_PRICE_ID="price_..."

# SendGrid (placeholder - needs real key)
SENDGRID_API_KEY="your_sendgrid_api_key"
SENDER_EMAIL="noreply@auditly.com"
```

### Frontend (/app/frontend/.env)
```bash
WDS_SOCKET_PORT=443
REACT_APP_BACKEND_URL=https://remediation-lab.preview.emergentagent.com
```

---

## 9. Database Collections

### users
```javascript
{
  id: "uuid",
  email: "user@example.com",
  full_name: "John Doe",
  hashed_password: "$2b$12$...",
  plan: "free",
  subscription_status: "inactive",
  stripe_customer_id: null,
  scans_used_this_month: 2,
  current_period_start: ISODate(),
  current_period_end: ISODate(),
  password_reset_token: null,
  password_reset_expires: null,
  created_at: ISODate()
}
```

### scan_requests
```javascript
{
  id: "uuid",
  url: "https://example.com",
  status: "completed",
  score: 88,
  issues: { passed: [...], failed: [...], incomplete: [...] },
  tool: "axe-core",
  user_id: "user-uuid",
  full_page_screenshot: "base64...",
  createdAt: ISODate()
}
```

---

## 10. Test Credentials

```
Email: test3@auditly.com
Password: testpass123
Plan: free (2 scans/month)
```

---

## 11. File Structure

```
/app/
├── backend/
│   ├── server.py           # All FastAPI routes, models, logic
│   ├── requirements.txt    # Python dependencies
│   └── .env               # Environment variables
├── frontend/
│   ├── src/
│   │   ├── App.js         # All React components
│   │   └── App.css        # Global styles + focus indicators
│   ├── package.json
│   └── .env
├── memory/
│   ├── PRD.md             # Product requirements
│   └── MASTER_ARCHITECTURE.md  # This file
└── test_reports/          # Testing agent outputs
```

---

## 12. Known Limitations & Pending Items

### Needs Production Keys
- [ ] Stripe API keys (payments not functional)
- [ ] SendGrid API key (emails logged to console in dev)

### Technical Debt
- [ ] Refactor App.js into /pages, /components, /contexts
- [ ] Refactor server.py into modular APIRouters
- [ ] Add routes for ForgotPasswordPage and ResetPasswordPage to App.js

### Future Features
- [ ] Team/organization accounts
- [ ] Scheduled recurring scans
- [ ] External API integrations (WAVE, EqualWeb, AccessiBe)
- [ ] Comparison reports between scans

---

## 13. Quick Start Commands

```bash
# Backend
cd /app/backend
pip install -r requirements.txt
sudo supervisorctl restart backend

# Frontend  
cd /app/frontend
yarn install
sudo supervisorctl restart frontend

# Check status
sudo supervisorctl status

# View logs
tail -f /var/log/supervisor/backend.err.log
tail -f /var/log/supervisor/frontend.err.log

# Test API
curl https://remediation-lab.preview.emergentagent.com/api/health
```

---

*Last Updated: March 23, 2026*
*Session: Implemented full auth system, Stripe subscriptions, WCAG-compliant UI, accessible PDF export, and password reset flow*
