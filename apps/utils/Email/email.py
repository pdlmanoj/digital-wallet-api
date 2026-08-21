import requests

from apps.core.config import settings
from apps.utils.Email.template import generate_email_template
from apps.utils.utils import EMAIL_VERIFICATION_OTP_EXPIRED_IN, generate_otp_and_save


class Email:
    """Email send for user registration using Maileroo"""

    def __init__(self) -> None:
        self.config = settings

    def get_headers(self) -> dict:

        return {
            "Authorization": f"Bearer {self.config.mailerro_key}",
            "Content-Type": "application/json",
        }

    def create_payload(self, email_to: str, email_template: str) -> dict:

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
            "subject": "Email OTP Verification (Digtal Wallet API)",
            "html": f"{email_template}",
        }

    def send_email(self, email: str):

        otp = generate_otp_and_save(email)
        otp_exp_minute = EMAIL_VERIFICATION_OTP_EXPIRED_IN // 60
        email_template = generate_email_template(otp, otp_exp_minute)
        headers = self.get_headers()
        payload = self.create_payload(email, email_template)

        response = requests.post(
            f"{self.config.maileroo_base_url}/emails", json=payload, headers=headers
        )

        return response


email = Email()
