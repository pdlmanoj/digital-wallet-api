# Digital Wallet API

A digital wallet REST API built with FastAPI. It currently supports user accounts, JWT authentication, optional 2FA authentication, wallets, deposits, withdrawals, and user-to-user transfers.

## Why?
I started this project, to learn how to build a production-grade backend from the ground up. Feedback, pull requests, ideas, and collaboration are welcome.

## Setup
1. Clone the repository and enter the project directory.

2. Install dependencies: ```uv sync```

3. Create the environment file: ```cp .env.sample .env```

4. Update `.env` with your PostgreSQL, Redis, JWT, 2FA, and email settings.

5. Apply the database migrations: ```uv run alembic upgrade head```

6. Run the API: ```uv run uvicorn apps.main:app --reload ```

The API is available at `http://127.0.0.1:8000`.

## Main API Areas

- `/user` - sign up, user lookup, OTP, and password management
- `/auth` - login, refresh tokens, current user, and 2FA
- `/wallet` - create and manage a wallet and check its balance
- `/transaction` - deposit, withdraw, and send money

Use Swagger UI at `/docs` for request schemas and interactive API testing.

## Run Tests

Tests use `TEST_DATABASE_URL`, so a test PostgreSQL database must be available and configured in `.env`.

```bash
uv run pytest
```

