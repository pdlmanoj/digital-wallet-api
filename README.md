# Digital Wallet API

A production-style wallet REST API built with FastAPI. It supports user accounts, JWT authentication, optional 2FA, wallets, deposits, withdrawals, and user-to-user transfers.
 
## Why I Built This
 
I built this project to learn how to design and build a production-grade backend from the ground up—not just an API that works, but one that is secure, reliable, and ready for real-world use.
 
 
## Features

- User registration, profile lookup, password change, password reset, and email OTP verification
- JWT access and refresh tokens, logout, and protected routes
- Optional 2FA setup, confirmation, verification, and disable flows
- One wallet per user with NPR balance management
- Deposits, withdrawals, and user-to-user transfers by phone number
- Recent transaction history with page and page-size pagination
- Profile image upload and expiring S3-compatible presigned URLs
- Admin-only user and wallet management endpoints
- Request rate limiting through Redis and SlowAPI
- Alembic migrations and Pytest integration tests

## Tech Stack
 
- **Language:** Python
- **Framework:** FastAPI
- **Database:** PostgreSQL
- **ORM:** SQLAlchemy
- **Migrations:** Alembic
- **Caching / Sessions:** Redis
- **Testing:** Pytest
- **Package Manager:** uv

## Getting Started

### Setup

```bash
git clone https://github.com/pdlmanoj/digital-wallet-api.git
cd digital-wallet-api
uv sync
cp .env.sample .env
uv run alembic upgrade head
uv run uvicorn apps.main:app --reload
```

Copy `.env.sample` to `.env` and add your PostgreSQL, Redis, JWT, 2FA, and email settings before running the migration.

The API runs at `http://127.0.0.1:8000`.
 
## API Overview
 
| Route | Description |
|---|---|
| `/user` | Sign up, user lookup, OTP, and password management |
| `/auth` | Login, refresh tokens, current user, and 2FA |
| `/wallet` | Create and manage a wallet, check balance |
| `/transaction` | Deposit, withdraw, and send money |
| `/manage` | Admin-only user and wallet management |
 
Full request/response schemas and interactive testing are available via Swagger UI at `/docs`.
 
## Running Tests
 
Configure `TEST_DATABASE_URL` in `.env`, then run:
 
```bash
uv run pytest
```
 
## Contributing
 
This is a learning project, but contributions are welcome. Feel free to open an issue or submit a pull request if you'd like to suggest a change or improvement.
 
