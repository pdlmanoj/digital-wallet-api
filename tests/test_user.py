from datetime import UTC, datetime, timedelta

import pytest
from faker import Faker

from apps.core.rate_limit import limiter
from tests.utils import mock_send_email, set_admin

limiter.enabled = False  # Disable rate limiting for tests

PASSWORD_HASH = "$2a$12$x54mYU7XnxeqFlWDmVDGoep.ebTSNze/0gn7i9f2DIP2z/yKiEKvS"
password = "my@password"
new_password = "new@password"

fake = Faker()
reference_id = fake.msisdn()


def test_signup(client):
    payload = {
        "name": "Jonam Ledule",
        "email": "jonam.ledule@gmail.com",
        "password": password,
        "phone_number": "9898989898",
        "gender": "male",
        "date_of_birth": "1990-01-01",
    }

    response = client.post("/user/signup", json=payload)

    assert response.status_code == 201

    assert response.json()["name"] == "Jonam Ledule"
    assert response.json()["phone_number"] == "9898989898"
    assert response.json().get("password") is None


def test_duplicate_signup(client):
    payload = {
        "name": "Jonam Ledule",
        "email": "jonam.ledule@gmail.com",
        "password": password,
        "phone_number": "9898989898",
        "gender": "male",
        "date_of_birth": "1990-01-01",
    }

    response = client.post("/user/signup", json=payload)

    assert response.status_code == 400
    assert response.json()["detail"]["error_type"] == "create_user.duplicate_user"


def test_user_login(client):
    response = client.post(
        "/auth/login", data={"username": "jonam.ledule@gmail.com", "password": password}
    )
    assert response.status_code == 200
    pytest.user_token = response.json().get("access_token")
    assert pytest.user_token is not None


def test_admin_signup(client, pg_db):
    payload = {
        "name": "Admin User",
        "email": "admin@gmail.com",
        "password": password,
        "phone_number": "9898989899",
        "gender": "male",
        "date_of_birth": "1990-01-01",
    }

    response = client.post("/user/signup", json=payload)
    phone_number = response.json().get("phone_number")
    set_admin(pg_db, phone_number)
    assert response.status_code == 201


def test_admin_login(client):
    response = client.post(
        "/auth/login", data={"username": "admin@gmail.com", "password": password}
    )
    assert response.status_code == 200
    pytest.admin_token = response.json().get("access_token")
    assert pytest.admin_token is not None


def test_user_not_found(client):
    response = client.get(f"/user/{fake.uuid4()}")
    assert response.status_code == 404
    assert response.json()["detail"]["error_type"] == "get_user.user_not_found"


def test_invalid_phone_number(client):
    payload = {
        "name": "Jonam Ledule",
        "email": "jonam.ledule@gmail.com",
        "password": password,
        "phone_number": "111111111111111",
        "gender": "male",
        "date_of_birth": "1990-01-01",
    }

    response = client.post("/user/signup", json=payload)
    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "string_too_long"


def test_invalid_date_of_birth(client):
    date_of_birth = datetime.now(UTC).date() + timedelta(days=1)
    payload = {
        "name": "Jonam Ledule",
        "email": "jonam.ledule@gmail.com",
        "password": password,
        "phone_number": "9898989898",
        "gender": "male",
        "date_of_birth": f"{date_of_birth}",
    }
    response = client.post("/user/signup", json=payload)
    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "value_error"


def test_password_length_failed(client):
    password = "short"
    payload = {
        "name": "Jonam Ledule",
        "email": "jonam.ledule@gmail.com",
        "password": password,
        "phone_number": "9898989898",
        "gender": "male",
        "date_of_birth": "1990-02-01",
    }
    response = client.post("/user/signup", json=payload)
    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "value_error"


def test_send_otp_success(mock_requests, client):

    mock_send_email(mock_requests)

    response = client.post("/user/send-otp", json={"email": "myemail@gmail.com"})

    assert response.status_code == 200


def test_send_otp_failed(client, mock_requests):

    mock_send_email(mock_requests, status="failed")

    response = client.post("/user/send-otp", json={"email": "testuser@gmail.com"})

    assert response.status_code == 400
    assert response.json()["detail"]["error_type"] == "send_otp.send_failed"


def test_resend_otp_success(client, mock_requests):

    mock_send_email(mock_requests)
    response = client.post("/user/resend-otp", json={"email": "resendemail@gmail.com"})
    assert response.status_code == 200


def test_resend_otp_failed(client, mock_requests):

    mock_send_email(mock_requests, status="failed")
    response = client.post("/user/resend-otp", json={"email": "resendemail@gmail.com"})
    assert response.status_code == 400
    assert response.json()["detail"]["error_type"] == "resend_otp.resend_failed"


def test_verify_otp_success(client, monkey_patch):
    def fake_validate_otp(email, otp):
        return True

    monkey_patch.setattr("apps.api.user.validate_otp", fake_validate_otp)
    response = client.post(
        "/user/verify-otp", json={"email": "test@gmail.com", "otp": "12345"}
    )
    assert response.status_code == 200


def test_verify_otp_failed(client):
    response = client.post(
        "/user/verify-otp", json={"email": "test@gmail.com", "otp": "322233443"}
    )
    assert response.status_code == 400
    assert response.json()["detail"]["error_type"] == "verify_otp.invalid_otp"


def test_get_users_failed(client):
    response = client.get(
        "/user/users", headers={"Authorization": f"Bearer {pytest.user_token}"}
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "You are not permitted to perfom this action."


def test_get_users_success(client):
    response = client.get(
        "/user/users", headers={"Authorization": f"Bearer {pytest.admin_token}"}
    )
    assert response.status_code == 200


def test_change_password_failed(client):
    payload = {
        "current_password": "",
        "new_password": "new@password",
    }

    response = client.post(
        "/user/change-password",
        headers={"Authorization": f"Bearer {pytest.user_token}"},
        json=payload,
    )

    assert response.status_code == 400
    assert (
        response.json()["detail"]["error_type"] == "change_password.password_too_short"
    )

    payload = {
        "current_password": password,
        "new_password": password,
    }
    response = client.post(
        "/user/change-password",
        headers={"Authorization": f"Bearer {pytest.user_token}"},
        json=payload,
    )
    assert response.status_code == 400
    assert response.json()["detail"]["error_type"] == "change_password.same_as_current"


def test_change_password_success(client):
    payload = {
        "current_password": password,
        "new_password": new_password,
    }

    response = client.post(
        "/user/change-password",
        headers={"Authorization": f"Bearer {pytest.user_token}"},
        json=payload,
    )

    assert response.status_code == 200


def test_forget_password_send_failed(client, mock_requests):
    mock_send_email(mock_requests, status="failed")
    response = client.post(
        "/user/forget-password", json={"email": "jonam.ledule@gmail.com"}
    )
    assert response.status_code == 400
    assert response.json()["detail"]["error_type"] == "forget_password.send_failed"


def test_forget_password_send_success(client, mock_requests):
    mock_send_email(mock_requests)
    response = client.post(
        "/user/forget-password", json={"email": "jonam.ledule@gmail.com"}
    )
    assert response.status_code == 200
