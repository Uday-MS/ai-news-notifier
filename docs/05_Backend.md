🔒 Architecture Decision Record
(ADR-001)(Backend)
Decision
We will build the backend as a Modular Monolith first, not as
Microservices.
This is one of the biggest architectural decisions for the startup.
Why?
Many startups think:
Startup
↓
Microservices
↓
Kubernetes
↓
100 Services
It looks impressive.
It usually becomes a nightmare.
Companies like these started as monoliths:
● Instagram
● GitHub
● Shopify
● Notion
● Basecamp
Only after they had millions of users did they split services.
Why Modular Monolith?
Imagine this.
Instead of:
Auth Server
News Server
AI Server
Notification Server
Search Server
Collector Server
Database
running separately...
We build:
One FastAPI Project
↓
Modules
↓
Auth
News
AI
Collector
Notification
Search
↓
One Database
Each module is independent.
But everything runs together.
Later...
When we have:
500,000 Users
we can simply move:
Collector
into its own service.
No redesign.
This is called:
Design for Microservices
Deploy as Modular Monolith
This is what I recommend.
What is Backend Architecture?
Think of the backend as the brain of the application.
User
↓
Frontend
↓
Backend
↓
Database
But our backend is much more than CRUD.
It is:
Authentication
↓
Collector
↓
AI
↓
Search
↓
Notifications
↓
Recommendation
↓
Database
Backend Philosophy
Let's define our principles.
Principle 1
Every module has one responsibility.
Principle 2
Modules should not know internal implementation details of other modules.
They communicate through clear interfaces.
Principle 3
Business logic stays in the backend.
Never in the frontend.
Principle 4
Frontend only displays data.
Backend makes decisions.
High-Level Backend Architecture
Frontend
│
▼
API Gateway (FastAPI)
│
────────────────────────────────────────────
Authentication Module
────────────────────────────────────────────
User Module
────────────────────────────────────────────
Event Module
────────────────────────────────────────────
Collector Module
────────────────────────────────────────────
AI Module
────────────────────────────────────────────
Search Module
────────────────────────────────────────────
Notification Module
────────────────────────────────────────────
Recommendation Module
────────────────────────────────────────────
Database Layer
Notice:
Every feature becomes a module.
Folder Structure
This is how I would organize it.
backend/
│
├── app/
│ ├── api/
│ ├── auth/
│ ├── users/
│ ├── events/
│ ├── organizations/
│ ├── collectors/
│ ├── ai/
│ ├── search/
│ ├── notifications/
│ ├── recommendations/
│ ├── database/
│ ├── models/
│ ├── schemas/
│ ├── services/
│ ├── core/
│ ├── utils/
│ └── config/
│
├── tests/
├── docs/
├── scripts/
└── migrations/
If a new developer joins, they immediately know where everything lives.
Backend Layers
This is where many beginners struggle.
Instead of writing everything in one file:
We separate layers.
API Layer
↓
Service Layer
↓
Repository Layer
↓
Database
API Layer
Receives HTTP requests.
Example:
GET /events
It validates input and calls the service.
Nothing more.
Service Layer
This is the brain.
Example:
User asks:
Latest Google AI News
↓
Service
↓
Checks permissions
↓
Fetches events
↓
Ranks events
↓
Returns response
No SQL here.
No HTTP here.
Just business logic.
Repository Layer
Only communicates with PostgreSQL.
Example:
SELECT *
FROM Events
WHERE importance > 90
Nothing else.
Database Layer
Stores information.
Nothing more.
Module Responsibilities
Authentication
Responsible for:
● Register
● Login
● JWT
● OAuth
● Password reset
● Email verification
User Module
Responsible for:
● Profile
● Interests
● Saved items
● Preferences
Event Module
Responsible for:
● News
● Research
● Opportunities
● Categories
● Tags
Collector Module
Responsible for:
● RSS
● APIs
● Website checks
● Schedulers
AI Module
Responsible for:
● Summaries
● Tags
● Classification
● Ranking
● Embeddings
Search Module
Responsible for:
● Full-text search
● Semantic search
● Filters
Notification Module
Responsible for:
● Push
● Email
● Deadlines
● Daily digest
Recommendation Module
Responsible for:
● Personalized feed
● Match scores
● Suggested opportunities
Request Flow
Imagine you open the app.
User
↓
Dashboard
↓
GET /dashboard
↓
API
↓
Dashboard Service
↓
Repositories
↓
Database
↓
AI Ranking
↓
JSON
↓
Frontend
This separation makes testing and maintenance much easier.
Why FastAPI?
We chose FastAPI because:
● Excellent performance.
● Automatic API documentation.
● Strong typing.
● Easy integration with AI libraries.
● Async support.
● Large ecosystem.
Error Handling
Never return raw exceptions.
Instead:
User
↓
Request
↓
Validation
↓
Business Logic
↓
Database
↓
Response
↓
Structured Error
For example:
{
"success": false,
"error": {
"code": "EVENT_NOT_FOUND",
"message": "Requested event does not exist."
}
}
Consistent responses make frontend development much easier.
Logging
Every important action should be logged:
● User login.
● Failed login.
● Collector failure.
● AI processing errors.
● Notification delivery.
● API exceptions.
This helps when debugging production issues.
Caching
We'll use Redis for:
● Dashboard data.
● Popular events.
● Search results.
● User sessions.
● AI outputs.
Caching reduces database load and improves response times.
Testing Strategy
Every module should have:
● Unit tests.
● Integration tests.
The goal is to catch issues before deployment.
Deployment Evolution
Here's how I expect the backend to evolve:
Phase 1
Single FastAPI application
↓
Phase 2
Background workers added
↓
Phase 3
Collector extracted
↓
Phase 4
AI service extracted
↓
Phase 5
Independent search service
Because we designed the modules well, each extraction is straightforward.