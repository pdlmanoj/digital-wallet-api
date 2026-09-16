from typing import Literal

import requests

from apps.core.config import mailerro
from apps.utils.Email.template import forget_password_template, signup_template
from apps.utils.utils import EMAIL_VERIFICATION_OTP_EXPIRED_IN, generate_otp_and_save


class Email:
    """Email send for user registration using Maileroo"""

    def __init__(self) -> None:
        self.config = mailerro

    def get_headers(self) -> dict:

        return {
            "Authorization": f"Bearer {self.config.mailerro_key}",
            "Content-Type": "application/json",
        }

    def create_payload(self, email_to: str, email_template: str, subject: str) -> dict:

        return {
            "from": {
                "address": f"sender@{self.config.maileroo_domain_email}",
                "display_name": "Digtal Wallet API",
            },
            "to": [
                {
                    "address": f"{email_to}",
                },
            ],
            "subject": subject,
            "html": f"{email_template}",
        }

    def send_email(
        self,
        email: str,
        password: str | None = None,
        type: Literal["signup", "forgot_password"] = "signup",
    ) -> requests.Response:
        if type not in ["signup", "forgot_password"]:
            raise ValueError(
                "Invalid email type. Must be 'signup' or 'forgot_password'."
            )

        headers = self.get_headers()

        if type == "signup":
            otp = generate_otp_and_save(email)
            otp_expire_in = EMAIL_VERIFICATION_OTP_EXPIRED_IN // 60
            email_template = signup_template(otp, otp_expire_in)
            subject = "Email OTP Verification (Digtal Wallet API)"

        elif type == "forgot_password" and password is not None:
            email_template = forget_password_template(password)
            subject = "Forgot Password (Digtal Wallet API)"

        payload = self.create_payload(email, email_template, subject)
        response = requests.post(
            f"{self.config.maileroo_base_url}/emails", json=payload, headers=headers
        )

        return response


email = Email()
