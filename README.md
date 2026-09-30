# Digital Wallet API

A production-style wallet REST API built with FastAPI. It supports user accounts, JWT authentication, optional 2FA, wallets, deposits, withdrawals, and user-to-user transfers.
 
## Why I Built This
 
I built this project to learn how a production-grade backend is designed and built from the ground up, not just how to make an API that works, but how to make one that is secure, reliable, and ready for real use.
 
 
## Features
 
- User signup and account management
- JWT-based authentication with access and refresh tokens
- Optional two-factor authentication (2FA)
- OTP verification and password reset
- Wallet creation and balance management
- Deposits, withdrawals, and peer-to-peer transfers

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
 
### 1. Clone the repository
 
```bash
git clone https://github.com/pdlmanoj/digital-wallet-api.git
cd digital-wallet-api
```
 
### 2. Install dependencies
 
```bash
uv sync
```
 
### 3. Set up environment variables
 
```bash
cp .env.sample .env
```
 
Then open `.env` and fill in your PostgreSQL, Redis, JWT, 2FA, and email settings.
 
### 4. Apply database migrations
 
```bash
uv run alembic upgrade head
```
 
### 5. Run the API
 
```bash
uv run uvicorn apps.main:app --reload
```
 
The API is now available at `http://127.0.0.1:8000`.
 
## API Overview
 
| Route | Description |
|---|---|
| `/user` | Sign up, user lookup, OTP, and password management |
| `/auth` | Login, refresh tokens, current user, and 2FA |
| `/wallet` | Create and manage a wallet, check balance |
| `/transaction` | Deposit, withdraw, and send money |
 
Full request/response schemas and interactive testing are available via Swagger UI at `/docs`.
 
## Running Tests
 
Tests use a separate `TEST_DATABASE_URL`, so make sure a test PostgreSQL database is set up and configured in `.env` before running them.
 
```bash
uv run pytest
```
 
## Contributing
 
This is a learning project, but contributions are welcome. Feel free to open an issue or submit a pull request if you'd like to suggest a change or improvement.
 
