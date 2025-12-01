# Customer Portal Design - Secure API Key Management

This document describes what a secure customer portal/dashboard would look like for API key management with 2FA.

## Overview

A customer portal is a web-based interface where customers can:
- View and manage their API keys securely
- Monitor usage and billing
- View account information
- Access audit logs
- All with 2FA/MFA protection

---

## UI/UX Design

### Login Page
```
┌─────────────────────────────────────────┐
│  Ollama API Gateway                     │
│  Customer Portal                        │
├─────────────────────────────────────────┤
│                                         │
│  Email: [laserpointlabs@gmail.com    ] │
│  Password: [••••••••••••••••••••••]    │
│                                         │
│  [ ] Remember me                        │
│                                         │
│  [  Sign In  ]                          │
│                                         │
│  Forgot password?                       │
└─────────────────────────────────────────┘
```

### 2FA Setup/Verification
```
┌─────────────────────────────────────────┐
│  Two-Factor Authentication              │
├─────────────────────────────────────────┤
│                                         │
│  Enter the 6-digit code from your      │
│  authenticator app:                     │
│                                         │
│  [ 0 ] [ 0 ] [ 0 ] [ 0 ] [ 0 ] [ 0 ]  │
│                                         │
│  [  Verify  ]                          │
│                                         │
│  Can't access your authenticator?        │
│  [ Use backup code ]                    │
└─────────────────────────────────────────┘
```

### Dashboard (Main View)
```
┌─────────────────────────────────────────────────────────────┐
│  Dashboard                          [John DeHart] [Logout] │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Account Overview                                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │ Monthly Usage │  │ Budget Status │  │ Active Keys  │   │
│  │   $45.23      │  │  $454.77     │  │      2       │   │
│  │  / $500.00    │  │  remaining   │  │              │   │
│  └──────────────┘  └──────────────┘  └──────────────┘   │
│                                                             │
│  API Keys                                    [Create Key]  │
│  ┌─────────────────────────────────────────────────────┐ │
│  │ Key Name: Production Key                              │ │
│  │ Created: Dec 1, 2024                                 │ │
│  │ Last Used: 2 hours ago                               │ │
│  │                                                       │ │
│  │ sk_example_abc123...xyz789                            │ │
│  │ [Show] [Copy] [Revoke]                               │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                             │
│  Recent Activity                                            │
│  ┌─────────────────────────────────────────────────────┐ │
│  │ Dec 1, 14:23 - API key created                      │ │
│  │ Dec 1, 12:15 - 1,234 requests processed            │ │
│  │ Nov 30, 18:45 - Budget warning (80% used)           │ │
│  └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### API Keys Management Page
```
┌─────────────────────────────────────────────────────────────┐
│  API Keys                          [Dashboard] [Settings]   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  [Create New API Key]                                       │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ Production Key                          [Active]    │  │
│  │ Created: Dec 1, 2024  |  Last Used: 2 hours ago   │  │
│  │ Requests: 12,345  |  Cost: $45.23                  │  │
│  │                                                      │  │
│  │ sk_example_abc123def456ghi789jkl012mno345pqr678stu901│  │
│  │ [Show Full Key] [Copy] [Regenerate] [Revoke]        │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ Development Key                        [Active]     │  │
│  │ Created: Nov 15, 2024  |  Last Used: 5 days ago    │  │
│  │ Requests: 234  |  Cost: $0.89                      │  │
│  │                                                      │  │
│  │ sk_example_xyz789abc123def456ghi789jkl012mno345pqr678│  │
│  │ [Show Full Key] [Copy] [Regenerate] [Revoke]        │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ Old Key (Revoked)                    [Revoked]      │  │
│  │ Created: Oct 1, 2024  |  Revoked: Nov 20, 2024    │  │
│  │ Requests: 8,901  |  Cost: $32.10                  │  │
│  └─────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Usage & Billing Page
```
┌─────────────────────────────────────────────────────────────┐
│  Usage & Billing                    [Dashboard] [API Keys]  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Current Period: December 2024                              │
│  Budget: $500.00  |  Used: $45.23  |  Remaining: $454.77 │
│  [████████░░░░░░░░░░░░░░░░░░░░░░░░░░] 9%                    │
│                                                             │
│  Usage by Model                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ llama3.2:1b      │  8,234 requests  │  $32.94      │  │
│  │ mistral           │  2,101 requests  │  $8.40       │  │
│  │ codellama         │  1,010 requests  │  $3.89       │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  Daily Usage Chart                                          │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  $5 │                                            │  │
│  │  $4 │        ██                                  │  │
│  │  $3 │    ████ ██                                  │  │
│  │  $2 │ ████ ██ ██                                  │  │
│  │  $1 │ ██ ██ ██ ██                                │  │
│  │  $0 └───────────────────────────────────────────  │  │
│  │     1  2  3  4  5  6  7  8  9 10 ...              │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  [Export CSV] [Export JSON] [View Full Report]             │
└─────────────────────────────────────────────────────────────┘
```

### Settings Page
```
┌─────────────────────────────────────────────────────────────┐
│  Account Settings                   [Dashboard] [API Keys]  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Profile Information                                         │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ Name:  [John DeHart                          ]      │  │
│  │ Email: [laserpointlabs@gmail.com             ]      │  │
│  │       [Update Email]                                 │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  Security                                                   │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ Two-Factor Authentication: [Enabled]                 │  │
│  │ [Manage 2FA]                                         │  │
│  │                                                      │  │
│  │ Password: [Change Password]                          │  │
│  │                                                      │  │
│  │ Backup Codes: [View/Regenerate]                     │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  Billing                                                    │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ Monthly Budget: [$500.00                    ]      │  │
│  │ [Update Budget]                                     │  │
│  │                                                      │  │
│  │ Budget Alerts: [Enabled]                            │  │
│  │ Alert at: [80%] [90%] [100%]                        │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  Audit Log                                                  │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ Dec 1, 14:23 - API key created                      │  │
│  │ Dec 1, 14:20 - Logged in from 192.168.1.100        │  │
│  │ Nov 30, 18:45 - Budget alert sent                   │  │
│  │ Nov 20, 10:15 - API key revoked                      │  │
│  └─────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## Architecture

### Backend Components

```
┌─────────────────────────────────────────────────────────┐
│                    FastAPI Backend                      │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  /portal/auth          - Authentication endpoints       │
│  /portal/keys          - API key management             │
│  /portal/usage         - Usage & billing data          │
│  /portal/settings      - Account settings               │
│  /portal/audit         - Audit log access               │
│                                                         │
│  Security Features:                                     │
│  - JWT tokens with refresh                              │
│  - 2FA via TOTP (Google Authenticator, Authy)          │
│  - Rate limiting                                        │
│  - CSRF protection                                       │
│  - Session management                                    │
│  - Audit logging                                        │
└─────────────────────────────────────────────────────────┘
```

### Database Schema Additions

```python
# New tables needed for portal

class PortalUser(Base):
    """Customer portal user account."""
    __tablename__ = "portal_users"
    
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), unique=True)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)  # bcrypt hashed
    two_factor_secret = Column(String, nullable=True)  # TOTP secret
    two_factor_enabled = Column(Boolean, default=False)
    backup_codes = Column(Text, nullable=True)  # JSON array, hashed
    last_login = Column(DateTime, nullable=True)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    customer = relationship("Customer", back_populates="portal_user")

class AuditLog(Base):
    """Audit log for security events."""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    event_type = Column(String, nullable=False)  # login, key_viewed, key_created, etc.
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    details = Column(Text, nullable=True)  # JSON
    created_at = Column(DateTime, default=datetime.utcnow)
    
    customer = relationship("Customer")
```

---

## API Endpoints

### Authentication

```python
# POST /portal/auth/register
# Register a new portal user (requires customer account)
{
    "email": "laserpointlabs@gmail.com",
    "password": "secure_password_123",
    "customer_id": 1  # Admin creates customer first
}

# POST /portal/auth/login
# Login with email/password
{
    "email": "laserpointlabs@gmail.com",
    "password": "secure_password_123"
}
# Returns: { "access_token": "...", "requires_2fa": true }

# POST /portal/auth/verify-2fa
# Verify 2FA code
{
    "token": "access_token_from_login",
    "code": "123456"
}
# Returns: { "access_token": "...", "refresh_token": "..." }

# POST /portal/auth/refresh
# Refresh access token
{
    "refresh_token": "..."
}

# POST /portal/auth/logout
# Logout (revoke tokens)
```

### API Key Management

```python
# GET /portal/keys
# List all API keys for authenticated customer
# Headers: Authorization: Bearer <token>
# Returns:
{
    "keys": [
        {
            "id": 5,
            "name": "Production Key",
            "created_at": "2024-12-01T14:23:00Z",
            "last_used": "2024-12-01T16:45:00Z",
            "active": true,
            "key_preview": "sk_example_abc123...xyz789",  # Masked
            "request_count": 12345,
            "total_cost": 45.23
        }
    ]
}

# POST /portal/keys
# Create new API key
{
    "name": "Production Key"
}
# Returns:
{
    "id": 6,
    "name": "Production Key",
    "api_key": "sk_example_full_key_here",  # Only shown once!
    "created_at": "2024-12-01T14:23:00Z"
}

# GET /portal/keys/{key_id}
# View full API key (requires 2FA re-verification)
# Headers: X-2FA-Code: 123456
# Returns:
{
    "id": 5,
    "api_key": "sk_live_full_key_here",
    "created_at": "2024-12-01T14:23:00Z",
    ...
}

# POST /portal/keys/{key_id}/regenerate
# Regenerate API key (revokes old, creates new)
# Requires 2FA confirmation
{
    "code": "123456"
}

# DELETE /portal/keys/{key_id}
# Revoke API key
# Requires 2FA confirmation
{
    "code": "123456"
}
```

### Usage & Billing

```python
# GET /portal/usage
# Get usage summary
{
    "current_period": {
        "start": "2024-12-01",
        "end": "2024-12-31",
        "total_cost": 45.23,
        "budget": 500.00,
        "remaining": 454.77,
        "percentage_used": 9.0
    },
    "by_model": [
        {
            "model": "llama3.2:1b",
            "requests": 8234,
            "cost": 32.94
        }
    ],
    "daily_usage": [
        {"date": "2024-12-01", "cost": 2.34},
        {"date": "2024-12-02", "cost": 3.45}
    ]
}

# GET /portal/usage/export?format=csv&start=2024-12-01&end=2024-12-31
# Export usage data
```

### Settings

```python
# GET /portal/settings
# Get account settings
{
    "name": "John DeHart",
    "email": "laserpointlabs@gmail.com",
    "budget": 500.00,
    "budget_alerts": [80, 90, 100],
    "two_factor_enabled": true
}

# PUT /portal/settings
# Update settings
{
    "name": "John DeHart",
    "budget": 750.00,
    "budget_alerts": [75, 90, 100]
}

# POST /portal/settings/2fa/setup
# Setup 2FA
# Returns:
{
    "secret": "JBSWY3DPEHPK3PXP",
    "qr_code": "data:image/png;base64,...",
    "backup_codes": ["code1", "code2", ...]
}

# POST /portal/settings/2fa/verify
# Verify and enable 2FA
{
    "code": "123456"
}

# POST /portal/settings/2fa/disable
# Disable 2FA (requires password + 2FA)
{
    "password": "...",
    "code": "123456"
}
```

---

## Security Features

### 1. Two-Factor Authentication (2FA)

**Implementation:**
- TOTP (Time-based One-Time Password) using `pyotp` library
- Compatible with Google Authenticator, Authy, 1Password, etc.
- Backup codes for account recovery
- Required for sensitive operations (viewing full keys, regenerating keys)

**Flow:**
1. User logs in with email/password
2. If 2FA enabled, server returns `requires_2fa: true`
3. User enters 6-digit code from authenticator app
4. Server verifies code and issues JWT tokens

### 2. Audit Logging

**Events Logged:**
- Login attempts (successful and failed)
- 2FA verification attempts
- API key creation/viewing/regeneration/revocation
- Settings changes
- Password changes
- Budget alerts

**Information Captured:**
- Timestamp
- Customer ID
- IP address
- User agent
- Event type
- Event details (JSON)

### 3. Rate Limiting

- Login attempts: 5 per 15 minutes per IP
- 2FA verification: 5 per 15 minutes per user
- API key operations: 10 per hour per user
- General API: 100 requests per minute per user

### 4. Session Management

- JWT tokens with short expiration (15 minutes)
- Refresh tokens with longer expiration (7 days)
- Token rotation on refresh
- Secure cookie storage for refresh tokens
- Logout revokes all tokens

### 5. Password Security

- Bcrypt hashing with salt
- Minimum password requirements (12+ chars, complexity)
- Password reset via email with time-limited tokens
- Password change requires current password + 2FA

---

## Frontend Implementation

### Technology Stack Options

**Option 1: React + TypeScript**
```bash
# Modern, component-based
- React 18+
- TypeScript
- Tailwind CSS or Material-UI
- React Router
- Axios for API calls
- React Query for data fetching
```

**Option 2: Vue.js**
```bash
# Simpler, easier to learn
- Vue 3
- TypeScript
- Vuetify or Tailwind CSS
- Vue Router
- Axios
```

**Option 3: Server-Side Rendered**
```bash
# FastAPI templates (simpler, less modern)
- Jinja2 templates
- HTMX for interactivity
- Alpine.js for JavaScript
- Tailwind CSS
```

### Example React Component

```typescript
// APIKeysList.tsx
import { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';

interface APIKey {
  id: number;
  name: string;
  created_at: string;
  last_used: string;
  active: boolean;
  key_preview: string;
  request_count: number;
  total_cost: number;
}

export function APIKeysList() {
  const { token } = useAuth();
  const [keys, setKeys] = useState<APIKey[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/portal/keys', {
      headers: { Authorization: `Bearer ${token}` }
    })
      .then(res => res.json())
      .then(data => {
        setKeys(data.keys);
        setLoading(false);
      });
  }, [token]);

  const handleRegenerate = async (keyId: number) => {
    const code = prompt('Enter 2FA code:');
    const res = await fetch(`/portal/keys/${keyId}/regenerate`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ code })
    });
    // Handle response...
  };

  return (
    <div className="api-keys-list">
      <h2>API Keys</h2>
      <button onClick={() => {/* Create new */}}>Create Key</button>
      {keys.map(key => (
        <div key={key.id} className="key-card">
          <h3>{key.name}</h3>
          <p>{key.key_preview}</p>
          <button onClick={() => handleRegenerate(key.id)}>Regenerate</button>
        </div>
      ))}
    </div>
  );
}
```

---

## Implementation Steps

### Phase 1: Basic Portal (MVP)
1. ✅ User registration/login
2. ✅ Password authentication
3. ✅ JWT token management
4. ✅ View API keys (masked)
5. ✅ Create new API keys
6. ✅ Basic usage dashboard

### Phase 2: Security (Essential)
1. ✅ 2FA setup and verification
2. ✅ Audit logging
3. ✅ Rate limiting
4. ✅ Session management
5. ✅ View full keys (with 2FA)

### Phase 3: Advanced Features
1. ✅ Regenerate keys
2. ✅ Revoke keys
3. ✅ Usage charts and analytics
4. ✅ Budget alerts
5. ✅ Export usage data
6. ✅ Account settings

### Phase 4: Polish
1. ✅ Email notifications
2. ✅ Password reset flow
3. ✅ Mobile-responsive design
4. ✅ Dark mode
5. ✅ Accessibility improvements

---

## Example Implementation

See `docs/portal_example/` for a complete example implementation with:
- FastAPI backend routes
- React frontend components
- Database migrations
- Docker setup
- Testing examples

---

## Security Checklist

- [ ] HTTPS only (TLS 1.2+)
- [ ] Secure password hashing (bcrypt)
- [ ] 2FA/MFA required for sensitive operations
- [ ] Rate limiting on all endpoints
- [ ] CSRF protection
- [ ] XSS protection (input sanitization)
- [ ] SQL injection prevention (parameterized queries)
- [ ] Audit logging for all sensitive actions
- [ ] Session timeout
- [ ] Secure cookie flags (HttpOnly, Secure, SameSite)
- [ ] Content Security Policy headers
- [ ] Regular security audits
- [ ] Penetration testing

---

## Deployment Considerations

### Environment Variables
```bash
PORTAL_SECRET_KEY=<random-secret-for-jwt>
PORTAL_2FA_ISSUER="Ollama API Gateway"
PORTAL_SESSION_TIMEOUT=900  # 15 minutes
PORTAL_RATE_LIMIT_ENABLED=true
PORTAL_AUDIT_LOG_RETENTION_DAYS=365
```

### Docker Setup
```yaml
# docker-compose.yml addition
portal:
  build: ./portal
  ports:
    - "8002:8000"
  environment:
    - DATABASE_URL=sqlite:////app/data/lmapi.db
    - PORTAL_SECRET_KEY=${PORTAL_SECRET_KEY}
  volumes:
    - ./data:/app/data
  depends_on:
    - api_gateway
```

---

## Cost Estimate

**Development Time:**
- Backend API: 40-60 hours
- Frontend UI: 60-80 hours
- Security features: 20-30 hours
- Testing: 20-30 hours
- **Total: 140-200 hours**

**Ongoing Maintenance:**
- Security updates: 4-8 hours/month
- Bug fixes: 4-8 hours/month
- Feature additions: Variable

---

This portal provides enterprise-grade security while maintaining a user-friendly experience for your customers.


