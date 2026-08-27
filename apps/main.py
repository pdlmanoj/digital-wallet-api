from pathlib import Path

from fastapi import FastAPI

from apps.api.auth import router as auth_router
from apps.api.transaction import router as transaction_router
from apps.api.user import router as user_router
from apps.api.wallet import router as wallet_router
from apps.core.config import settings

# Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.app_name, version=settings.app_version, debug=settings.debug
)

app.include_router(user_router)
app.include_router(auth_router)
app.include_router(wallet_router)
app.include_router(transaction_router)


# TODO: add CROS origin protection


@app.get("/")
def test():
    return {"msg": "Hello World"}


@app.get("/health-check")
def check():
    return {
        "msg": "Success",
        "app": settings.app_name,
        "debug": settings.debug,
        "db_url": settings.database_url.unicode_string(),
        "base": Path(__file__).parent.parent,
    }
