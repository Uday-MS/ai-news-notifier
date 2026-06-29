Phase 10 – Deployment & DevOps
Architecture
First Architecture Decision (ADR-004)
Before discussing Docker, cloud, or CI/CD, I want to make an important decision.
Cloud Native from Day One
This means:
● We build locally.
● We deploy exactly the same way in production.
● We never redesign just because we move to the cloud.
This avoids the classic:
"It works on my machine."
problem.
What is DevOps?
Think of it like this.
Without DevOps:
Developer
↓
Writes Code
↓
Uploads Files
↓
Server
↓
Hope it Works
With DevOps:
Developer
↓
GitHub
↓
Automatic Testing
↓
Build
↓
Deploy
↓
Monitor
↓
Alert
↓
Production
Everything becomes automated and repeatable.
Deployment Philosophy
Our deployment should follow five principles.
1. Repeatable
Every deployment should produce the same result.
2. Automated
Avoid manual steps wherever possible.
3. Reversible
If something breaks,
one click should roll back to the previous version.
4. Observable
Know:
● CPU usage
● Memory
● Errors
● API latency
● Collector failures
at all times.
5. Scalable
Today:
100 users
Tomorrow:
100,000 users
The architecture should evolve without a complete redesign.
Overall Infrastructure
Here's the complete picture.
Users
↓
Internet
↓
Domain
↓
HTTPS
↓
CDN (future)
↓
Frontend
↓
API
↓
Redis
↓
PostgreSQL
↓
Background Workers
↓
Collector
↓
AI Pipeline
↓
Storage
↓
Monitoring
Every component has a clear responsibility.
Development Environments
We'll maintain four environments.
Local
↓
Development
↓
Staging
↓
Production
Local
Your laptop.
Development
Shared environment for active development.
Staging
A copy of production used for final testing.
Production
The live system users access.
This separation reduces the risk of accidental production issues.
Docker Strategy
Everything runs inside containers.
Examples:
Frontend
↓
Docker
Backend
↓
Docker
Redis
↓
Docker
PostgreSQL
↓
Docker
Collector
↓
Docker
Containers make local development and production much more consistent.
Docker Compose (MVP)
Initially, one command should start the entire application.
Example services:
● Frontend
● Backend
● PostgreSQL
● Redis
● Background worker
This gives every developer the same environment.
CI/CD Pipeline
Every code change follows this path.
Developer
↓
Git Push
↓
GitHub
↓
CI
↓
Tests
↓
Build
↓
Deploy
↓
Health Check
↓
Production
No manual uploads.
Branch Strategy
We'll use:
main
↓
develop
↓
feature/*
Rules:
● main is always deployable.
● Features merge into develop.
● Releases merge into main after review.
Database Migrations
Never modify the production database manually.
Instead:
Code
↓
Migration
↓
Deploy
↓
Database Updated
Every schema change is version-controlled.
Secrets Management
Never commit secrets to Git.
Examples:
● Database credentials
● JWT signing keys
● AI API keys
Use environment variables or a secrets manager.
Logging
Every service writes structured logs.
Examples:
● Login attempts
● Collector activity
● AI processing
● Errors
● Notification delivery
This makes debugging production much easier.
Monitoring
Track:
● API response time
● Collector health
● Queue length
● AI processing time
● Database performance
● Error rates
Monitoring should tell us before users notice a problem.
Backups
Regular backups are essential.
Plan for:
● Scheduled database backups.
● Restore testing.
● Disaster recovery procedures.
Backups are only useful if you know they can be restored.
Storage
Separate storage from the application.
Examples:
● Images
● Logos
● Cached files
● Attachments
This keeps deployments lightweight.
Scaling Roadmap
Stage 1 (MVP)
One server.
Everything together.
Frontend
Backend
Redis
PostgreSQL
Simple and inexpensive.
Stage 2
Move background workers to their own process.
Collector and AI tasks no longer compete with API requests.
Stage 3
Separate services.
● Collector
● AI
● Search
can each scale independently.
Stage 4
Add read replicas, caching improvements, and more advanced infrastructure as user growth
demands it.
DevOps Checklist
Before every release:
● Tests pass.
● Migrations reviewed.
● Environment variables verified.
● Backups confirmed.
● Health checks configured.
● Rollback plan ready.
This checklist reduces deployment risk.
One Improvement I'd Add
I'd introduce a small Operations Dashboard (separate from the Admin Portal).
The Admin Portal manages business content.
The Operations Dashboard monitors the platform itself.
It would show:
● Service status.
● Queue health.
● Collector status.
● AI processing metrics.
● Database connectivity.
● Deployment version.
● Error rates.
● Uptime.
This separation keeps operational concerns distinct from administrative tasks.
Architecture Decision Record (ADR-004)
Decision
Docker-first deployment with automated CI/CD and environment isolation.
Reason:
● Consistent developer environments.
● Reliable deployments.
● Easier onboarding.
● Smooth transition from MVP to production.
My Technology Recommendations
Here's what I'd use for the MVP.
Area Recommendation
Frontend Hosting Vercel
Backend Hosting Railway or Render
Database PostgreSQL
Cache Redis
Storage Cloud object storage (e.g., S3-compatible)
CI/CD GitHub Actions
Containers Docker + Docker Compose
Monitoring Uptime monitoring + application logs (expand later)
Reverse Proxy Nginx (if self-hosting)
These services are easy to start with and can be replaced or expanded later if your scale
requires it.
Current Architecture Status
Vision ✅
PRD ✅
UI/UX ✅
Database 🔒 Blueprint Locked
Backend 🔒 Blueprint Locked
API 🔒 Blueprint Locked
AI Pipeline ✅
Collector ✅
Security ✅
Deployment & DevOps ✅