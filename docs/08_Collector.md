So What Is The Collector?
Think of it as your company's reporters.
It never sleeps.
Every few minutes it checks trusted sources.
Imagine:
Anthropic
↓
Collector
↓
New Blog
↓
Database
Same for:
Google
↓
Collector
↓
New Internship
↓
Database
Collector Philosophy
Every collector has ONE responsibility.
Never make one huge collector.
Instead:
Collector Engine
│
├── RSS Collector
├── GitHub Collector
├── Career Collector
├── Research Collector
├── YouTube Collector
├── API Collector
└── Future Plugins
This plugin approach means adding a new source is straightforward.
Data Flow
Source
↓
Collector
↓
Parser
↓
Normalizer
↓
Duplicate Checker
↓
AI Pipeline
↓
Database
↓
Notification
↓
User
The collector's job ends once it hands normalized data to the AI pipeline.
Step 1 — Source Registry
The collector should not have URLs hardcoded.
Instead, we maintain a Source Registry.
Every source contains:
● Organization
● Source type (RSS, API, Careers, YouTube, etc.)
● URL
● Polling frequency
● Authentication method (if needed)
● Priority
● Status (active/inactive)
This allows us to manage sources without changing code.
Step 2 — Scheduler
The collector runs on schedules, not continuously.
Examples:
● High-priority sources every 10–15 minutes.
● Medium-priority sources every hour.
● Low-priority sources daily.
This balances freshness with infrastructure costs.
Step 3 — Normalization
Every source returns different data.
Example:
RSS:
Title
Description
Date
GitHub:
Repository
Stars
Language
Career Page:
Job
Deadline
Location
We convert all of these into a common internal Event format before sending them to the AI
pipeline.
Step 4 — Retry Strategy
Network requests fail.
Instead of giving up:
Attempt 1
↓
Failed
↓
Wait
↓
Attempt 2
↓
Failed
↓
Wait Longer
↓
Attempt 3
↓
Alert
Retries should use exponential backoff to avoid overwhelming external services.
Step 5 — Source Health
Each source gets a health status.
Examples:
🟢 Healthy
🟡 Slow
🔴 Failed
If a source repeatedly fails, the system flags it for review.
Step 6 — Queue
Imagine 100 sources publish updates simultaneously.
We don't want one huge synchronous process.
Instead:
Collector
↓
Queue
↓
Workers
↓
AI Pipeline
Each worker processes events independently, improving scalability.
Step 7 — Deduplication Before AI
If the same event is collected twice,
don't summarize it twice.
Duplicate detection should happen as early as possible to save AI costs.
Step 8 — Monitoring
We should track:
● Last successful collection.
● Collection duration.
● Number of new events.
● Failed requests.
● Retry counts.
This helps diagnose issues quickly.
One Improvement I'd Like to Add
I want the collector to support connectors instead of source-specific code.
Think of connectors as interchangeable modules.
Connector Interface
↓
RSS Connector
API Connector
GitHub Connector
YouTube Connector
Careers Connector
Research Connector
Every connector implements the same methods:
● Fetch latest content.
● Validate data.
● Normalize to our event schema.
● Return results.
This makes the collector highly extensible.