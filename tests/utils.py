from typing import Literal

from faker import Faker

from apps.core.config import mailerro

MAILEROO_BASE_URL = mailerro.maileroo_base_url
fake = Faker()


def mock_otp(mock_requests, status: Literal["success", "failed"] = "success"):
    reference_id = fake.msisdn()
    mock_requests.post(
        f"{MAILEROO_BASE_URL}/emails",
        json={"reference_id": reference_id, "success": status == "success"},
        status_code=200 if status == "success" else 400,
    )
