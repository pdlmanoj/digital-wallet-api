from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded

from apps.api.auth import router as auth_router
from apps.api.transaction import router as transaction_router
from apps.api.user import router as user_router
from apps.api.wallet import router as wallet_router
from apps.core.config import settings
from apps.core.rate_limit import customer_rate_limit_exception_handler, limiter

swagger_ui_parameters = {
    "defaultModelsExpandDepth": -1,  # Disable Schemas shown in Swagger
    "displayRequestDuration": True,  # display execution time next to response status code
    "persistAuthorization": True,  # keeps logged even after brower reload
}

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    swagger_ui_parameters=swagger_ui_parameters,
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, customer_rate_limit_exception_handler)

# Allow the web frontend to call this API from a browser.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,  # we use Authorization headers, not cookies
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_router)
app.include_router(auth_router)
app.include_router(wallet_router)
app.include_router(transaction_router)


@app.get("/health-check")
def health_check(request: Request):
    return {
        "msg": "Success",
        "app": settings.app_name,
        "debug": settings.debug,
    }
