from typing import Literal

from faker import Faker
from sqlalchemy.orm import Session

from app.core.config import mailerro
from app.models.user import User

MAILEROO_BASE_URL = mailerro.maileroo_base_url
fake = Faker()


def mock_send_email(mock_requests, status: Literal["success", "failed"] = "success"):
    reference_id = fake.msisdn()
    mock_requests.post(
        f"{MAILEROO_BASE_URL}/emails",
        json={"reference_id": reference_id, "success": status == "success"},
        status_code=200 if status == "success" else 400,
    )


def set_admin(db: Session, phone_number: str):
    user = db.query(User).filter_by(phone_number=phone_number).first()
    if user:
        user.is_admin = True
        db.commit()
