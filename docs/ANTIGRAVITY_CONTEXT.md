# AI News Notifier – Antigravity Context

## Project Overview

AI News Notifier is an AI-powered intelligence platform designed for students, developers, researchers, and professionals.

The platform collects information only from trusted and official sources, processes it through an AI pipeline, ranks its importance, and delivers personalized recommendations.

The goal is not to build a traditional news website but an AI intelligence platform.

---

## Tech Stack

### Frontend

* React
* TypeScript
* Tailwind CSS
* Modern responsive UI

### Backend

* FastAPI
* Python

### Database

* PostgreSQL

### Cache

* Redis

### Authentication

* JWT Access Token
* Refresh Token
* Google OAuth
* Role Based Access Control (RBAC)

### Infrastructure

* Docker
* Docker Compose
* GitHub Actions

---

## Backend Architecture

Follow Modular Monolith architecture.

Modules include:

* Authentication
* Users
* Events
* Collector
* AI
* Search
* Notifications
* Recommendations

Every module must follow:

* API Layer
* Service Layer
* Repository Layer
* Database Layer

Business logic must remain inside the backend.

---

## Coding Principles

* Clean Architecture
* SOLID Principles
* Strong typing
* Proper validation
* Consistent folder structure
* Secure by default

---

## Authentication Standards

Implement:

* Register
* Login
* JWT Authentication
* Refresh Token
* Password Hashing
* Google OAuth structure
* Forgot Password architecture
* Reset Password architecture
* Email verification architecture
* RBAC foundation

---

## UI Guidelines

When screenshots are provided, recreate the layout as closely as possible while keeping the implementation clean, responsive, and component-based.

Do not hardcode styles unnecessarily.

---

## Output Expectations

Generate production-quality code.

Follow the existing repository structure.

Do not create a different architecture.

Reuse components where possible.

Add meaningful comments only where necessary.

Generate code that is maintainable, scalable, and ready for future modules.
