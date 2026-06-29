🔒 Security & Authentication
Architecture
Before we discuss technologies, I want to define our philosophy.
Security Philosophy
Our goal is not just to protect passwords.
Our goal is to protect:
● User accounts
● User preferences
● Saved opportunities
● AI recommendations
● Internal APIs
● Admin panel
● Collector service
● Database
● AI API keys
● Infrastructure
Security applies to the entire platform.
Security Layers
Think of the platform like a building.
Internet
│
▼
Firewall / Hosting
│
▼
HTTPS
│
▼
API Gateway
│
▼
Authentication
│
▼
Authorization
│
▼
Business Logic
│
▼
Database
Every layer protects the next.
Authentication vs Authorization
Many people confuse these.
Authentication answers:
Who are you?
Authorization answers:
What are you allowed to do?
Example:
User logs in.
Authentication:
✅ Chiku verified.
Now:
Authorization:
Can Chiku access
Admin Dashboard?
❌ No
Saved Opportunities?
✅ Yes
User Authentication Flow
I recommend supporting:
MVP
● Email + Password
● Google Sign-In
Later
● GitHub
● Microsoft
● University SSO
Login Flow
User
↓
Login
↓
Validate Input
↓
Find User
↓
Verify Password
↓
Generate JWT
↓
Generate Refresh Token
↓
Return Tokens
Password Security
Never store passwords.
Ever.
Instead:
Password
↓
Hash
↓
Database
During login:
Password
↓
Hash
↓
Compare
↓
Success
Even if the database leaks,
passwords remain protected.
JWT Strategy
I recommend:
Access Token
● Short lifetime
Refresh Token
● Longer lifetime
Example:
Access
15 minutes
Refresh
7 days
The frontend silently refreshes the access token when needed.
Email Verification
Every new account should verify its email before becoming fully active.
Benefits:
● Reduces fake accounts.
● Ensures password recovery works.
● Improves trust.
Forgot Password
Flow:
User
↓
Forgot Password
↓
Email Link
↓
Temporary Token
↓
Reset Password
↓
Invalidate Old Sessions
Never send passwords by email.
Role-Based Access Control (RBAC)
We'll define roles.
User
Can:
● Read news.
● Save opportunities.
● Update profile.
Moderator (Future)
Can:
● Review AI summaries.
● Approve content.
● Manage sources.
Admin
Can:
● Manage organizations.
● Manage collectors.
● View analytics.
● Configure platform.
This makes future expansion easier.
API Security
Every protected endpoint checks:
1. Valid JWT.
2. User role.
3. Permissions.
No exceptions.
Rate Limiting
Protect against abuse.
Examples:
Login:
5 attempts per minute.
Search:
100 requests per minute.
API:
Configurable limits by endpoint.
Input Validation
Never trust user input.
Validate:
● Email
● Password
● Search queries
● IDs
● File uploads
This prevents many common attacks.
Secrets Management
Never commit secrets to Git.
Examples:
● AI API keys.
● Database passwords.
● JWT signing keys.
Store them securely using environment variables or a dedicated secrets manager.
Audit Logs
Record important actions.
Examples:
● Login
● Password change
● Email change
● Admin actions
● Source modifications
This helps with troubleshooting and security reviews.
Collector Security
The collector should:
● Respect API limits.
● Identify itself appropriately where required.
● Store credentials securely.
● Retry responsibly.
● Log failures.
Database Security
Use the principle of least privilege.
Application account:
● Read/write application tables.
● No unnecessary administrative privileges.
Separate administrative credentials for maintenance tasks.
HTTPS Everywhere
All traffic should be encrypted.
No HTTP in production.
Session Management
When a user changes their password:
● Existing refresh tokens become invalid.
● Active sessions can be revoked.
This reduces account takeover risk.
Security Headers
The application should include standard security headers to reduce browser-based attacks.
Examples include protections against clickjacking and content injection.
Logging & Monitoring
Security monitoring should detect:
● Repeated failed logins.
● Unusual API usage.
● Unexpected collector failures.
● Suspicious admin activity.
Alerts can be added as the platform grows.
One Improvement I'd Add
I'd introduce a Security Middleware Layer.
Every request passes through:
Request
↓
HTTPS Check
↓
Rate Limiter
↓
Authentication
↓
Authorization
↓
Validation
↓
Business Logic
↓
Response
This keeps security centralized instead of scattering checks across the codebase.
Architecture Decision Record (ADR-003)
Decision
JWT + Refresh Tokens + RBAC
Reason:
● Stateless authentication.
● Easy scaling.
● Industry-standard approach.
● Works well with web and future mobile apps.
Security Roadmap
MVP
● Email login
● Google login
● JWT
● Refresh tokens
● Password hashing
● Email verification
● Forgot password
● RBAC
● HTTPS
● Rate limiting
● Input validation
Post-MVP
● Two-factor authentication
● Device/session management UI
● Login alerts
● Security dashboard
● Advanced anomaly detection