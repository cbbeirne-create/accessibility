# Test Credentials

## Test Users

### Verified User
- **Email:** verifytest@example.com
- **Password:** testpassword123
- **Status:** Email verified

### Unverified User  
- **Email:** newverify@example.com
- **Password:** testpassword123
- **Status:** Email not verified (can test verification banner)

### Original Test User
- **Email:** testuser@example.com
- **Password:** newpassword456
- **Status:** Created before email verification feature (email_verified: false by default)

## Notes
- All users are on the FREE plan (2 scans/month)
- SendGrid is **MOCKED** - verification links are logged to `backend.err.log`
- Stripe is **MOCKED** - payments will return 503 error
