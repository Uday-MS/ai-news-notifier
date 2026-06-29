TESTING
I think we're entering one of the most underestimated parts of software engineering.
Most college projects do this:
Write Code
↓
Run Once
↓
Works
↓
Done
Real software companies do this:
Write Code
↓
Test
↓
Fix
↓
Test Again
↓
Deploy
↓
Monitor
↓
Improve
That difference is why one becomes a demo and the other becomes a product.
🧪 Phase 11 – Testing Strategy
Testing Philosophy
I don't want testing to be something we do at the end.
Testing starts while we build.
Every feature we develop should have its own tests.
Testing Pyramid
This is one of the most widely accepted strategies.
Manual Testing
▲
End-to-End Tests
▲
Integration Tests
▲
Unit Tests
Most tests should be Unit Tests because they're fast and catch problems early.
Phase 1 — Unit Testing
Test one function or class at a time.
Examples:
Authentication
Login()
↓
Valid Password?
↓
PASS
AI
Summary()
↓
Returns Summary?
↓
PASS
Recommendation
Importance Score()
↓
Correct?
↓
PASS
Phase 2 — Integration Testing
Now test modules working together.
Example:
Collector
↓
Database
↓
PASS
Example:
AI
↓
Database
↓
PASS
Example:
User
↓
Notifications
↓
PASS
Phase 3 — API Testing
Every endpoint should be tested.
Example
GET /api/v1/events
Expected:
{
"success": true
}
Wrong authentication?
Expected:
401 Unauthorized
Every endpoint should have:
● Success case
● Validation failure
● Authorization failure
● Not found
● Server error
Phase 4 — End-to-End Testing
Pretend you're a user.
Register
↓
Verify Email
↓
Login
↓
Set Interests
↓
Dashboard
↓
Save Opportunity
↓
Receive Notification
The whole journey should work.
Phase 5 — AI Testing
This is unique to our platform.
We're not just testing code.
We're testing AI quality.
Examples:
Summary Quality
Original:
2000 words
Summary:
Correct?
Missing important information?
Hallucinations?
Classification
Article:
Claude 6
Expected:
MODEL_RELEASE
Not:
HACKATHON
Tags
Expected:
Anthropic
Claude
LLM
Reasoning
Recommendation
User:
Interested in Google
Google Internship
Expected:
High Match
Not:
Low Match
Phase 6 — Collector Testing
Collector tests should include:
● RSS parsing.
● API parsing.
● Retry logic.
● Timeout handling.
● Duplicate detection.
● Normalization.
Phase 7 — Database Testing
Verify:
● Constraints.
● Relationships.
● Migrations.
● Index usage.
● Data integrity.
Phase 8 — Security Testing
Test:
● Invalid JWT.
● Expired JWT.
● Missing JWT.
● SQL Injection attempts.
● XSS attempts.
● Rate limiting.
● Unauthorized access.
These tests help ensure the platform behaves safely under malicious input.
Phase 9 — Performance Testing
Questions we want to answer:
Dashboard loads in:
< 2 seconds
Search:
< 500 ms
Collector:
Can process many sources without falling behind.
Phase 10 — Load Testing
Imagine:
1000 Users
↓
Login
↓
Dashboard
↓
Search
Does the system stay responsive?
Then:
10000 Users
We identify bottlenecks before they affect users.
Phase 11 — Usability Testing
Ask students to use the platform.
Observe:
● Can they find opportunities?
● Do they understand notifications?
● Is the dashboard intuitive?
This feedback often reveals issues that technical tests cannot.
Phase 12 — Beta Testing
A limited group of real users.
Examples:
● Friends.
● College classmates.
● Professors.
● Developers.
Collect:
● Bugs.
● Suggestions.
● Confusing workflows.
● Performance feedback.
Bug Lifecycle
Every bug follows a consistent path.
Found
↓
Reported
↓
Verified
↓
Assigned
↓
Fixed
↓
Retested
↓
Closed
Tracking this process prevents issues from being forgotten.
Testing Checklist
Before Version 1.0:
Authentication
✅
Dashboard
✅
Collector
✅
AI Pipeline
✅
Search
✅
Notifications
✅
Security
✅
Performance
✅
Deployment
✅
Documentation
✅
Only after all items are complete do we launch.
Testing Tools (Recommended)
Area Suggested Tool
Backend Unit Tests pytest
API Testing pytest + FastAPI TestClient
Frontend Component
Tests
Vitest
End-to-End Testing Playwright
Load Testing k6
Code Coverage pytest-cov
Static Analysis Ruff + MyPy
These tools fit well with the technology stack we've chosen.
Continuous Testing
Testing shouldn't happen once.
Every GitHub Pull Request should automatically:
Code Push
↓
Unit Tests
↓
Integration Tests
↓
Lint
↓
Coverage
↓
PASS
↓
Merge
If tests fail,
merge is blocked.
Architecture Decision Record (ADR-005)
Decision
Every feature must include automated tests before it is considered complete.
Reason:
● Better reliability.
● Easier refactoring.
● Higher confidence during releases.
● Faster debugging.