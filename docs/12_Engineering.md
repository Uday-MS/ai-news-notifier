📘 Phase 12 – Engineering Standards &
Development Guidelines
Our Engineering Philosophy
Every line of code should be:
● Readable.
● Maintainable.
● Testable.
● Secure.
● Documented.
● Consistent.
The goal is that a developer joining six months from now should be able to understand the
project without needing someone to explain everything.
1. Git Workflow
We'll follow a simplified Git Flow.
main
│
├── develop
│
├── feature/authentication
├── feature/dashboard
├── feature/collector
├── feature/search
├── feature/notifications
└── feature/...
Branch Rules
● main → Production-ready code only.
● develop → Integration branch for completed features.
● feature/* → One feature per branch.
● hotfix/* → Emergency production fixes.
● release/* → Preparing a production release.
2. Commit Message Standard
We should use clear, conventional commit messages.
Examples:
feat(auth): add Google OAuth login
fix(api): resolve pagination bug
docs(database): update ER diagram
test(search): add search API tests
refactor(events): simplify event ranking service
chore(ci): update GitHub Actions workflow
Benefits:
● Easier release notes.
● Better Git history.
● Simpler debugging.
3. Pull Request Rules
Every pull request should include:
● Clear description.
● Screenshots (if UI changes).
● Related issue/task.
● Testing performed.
● Any migration notes.
No direct pushes to main.
4. Code Review Checklist
Before approving code, reviewers should check:
● Correctness.
● Readability.
● Security.
● Performance.
● Error handling.
● Tests.
● Documentation.
Reviews should improve the code, not just approve it.
5. Coding Standards
Python
● Use type hints.
● Follow PEP 8.
● Keep functions focused.
● Avoid duplicated logic.
TypeScript
● Enable strict mode.
● Prefer interfaces for shared contracts.
● Avoid any unless absolutely necessary.
6. Naming Conventions
Consistency matters.
Files
user_service.py
event_repository.py
notification_controller.py
Classes
UserService
EventRepository
NotificationManager
Variables
user_id
event_title
notification_count
Avoid abbreviations that reduce clarity.
7. Folder Structure
Every module should follow the same layout.
events/
│
├── api.py
├── service.py
├── repository.py
├── models.py
├── schemas.py
├── tests/
└── utils.py
Developers should know where to find things without guessing.
8. API Standards
Every endpoint should:
● Be versioned.
● Return consistent responses.
● Validate inputs.
● Use proper HTTP status codes.
● Document request and response schemas.
9. Database Standards
● Use snake_case for table and column names.
● Primary key: id.
● Foreign keys: <entity>_id.
● Add timestamps (created_at, updated_at) where appropriate.
● Never modify production data directly.
10. Documentation Standards
Every feature should include:
● Purpose.
● Design decisions (if significant).
● API changes.
● Database changes.
● Testing notes.
Code comments should explain why, not just what.
11. Definition of Done (DoD)
A feature is complete only if:
● Functionality implemented.
● Unit tests written.
● Integration tests pass (if applicable).
● Code reviewed.
● Documentation updated.
● Security considerations checked.
● No critical linting errors.
● CI pipeline passes.
Only then is it merged into develop.
12. Issue Tracking
Every task should have:
● Title.
● Description.
● Priority.
● Assignee.
● Labels.
● Status.
Example workflow:
Backlog
↓
Ready
↓
In Progress
↓
Code Review
↓
Testing
↓
Done
13. Versioning
We'll use Semantic Versioning.
Examples:
v1.0.0
Initial Release
v1.1.0
New Features
v1.1.1
Bug Fix
v2.0.0
Breaking Changes
This makes releases predictable.
14. Dependency Management
Only add a dependency if:
● It solves a real problem.
● It is actively maintained.
● It has good documentation.
● It fits our licensing requirements.
Avoid adding libraries just for convenience.
15. Security Standards
Every new feature must consider:
● Authentication.
● Authorization.
● Input validation.
● Sensitive data handling.
● Logging.
Security reviews should be part of development, not an afterthought.
16. Performance Standards
Set measurable expectations.
Examples:
● Dashboard: target under 2 seconds.
● Search: target under 500 ms.
● API response: target under 300 ms for common endpoints.
These are goals to monitor as the system evolves.
17. Engineering Documentation
Every major technical decision should result in:
● Updated architecture docs (if needed).
● ADR (Architecture Decision Record) when appropriate.
● Changelog entry for releases.
This keeps the project understandable over time.
18. Team Communication
I recommend a simple rhythm:
● Short weekly planning meeting.
● Mid-week technical sync if needed.
● End-of-week demo or progress review.
For a student startup, this is usually enough without creating unnecessary overhead.
Architecture Decision Record (ADR-006)
Decision
Engineering standards are mandatory for every contribution, regardless of team size.
Reason:
● Consistent codebase.
● Easier onboarding.
● Better maintainability.
● Higher product quality.
Engineering Standards Checklist
Before merging any feature:
● Code compiles.
● Tests pass.
● Linting passes.
● Documentation updated.
● Reviewer approval received.
● No unresolved critical comments.
● CI/CD pipeline green.