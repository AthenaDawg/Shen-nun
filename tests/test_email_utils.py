import pytest
from unittest.mock import patch
from app.email_utils import send_reset_password_email, send_email_confirm_token


class DummyUser:
    def __init__(self, email):
        self.email = email

    def get_reset_token(self):
        return "reset-token"

    def get_email_confirm_token(self):
        return "confirm-token"


@pytest.fixture
def user():
    return DummyUser("test@example.com")


@patch('app.email_utils.mail.send')
def test_send_reset_email(mock_send, user, app):
    with app.app_context():
        send_reset_password_email(user)
        assert mock_send.called


@patch('app.email_utils.mail.send', side_effect=Exception("SMTP error"))
@patch('app.email_utils.logging.error')
def test_send_reset_email_exception(mock_log_error, mock_send, user, app):
    with app.app_context():
        send_reset_password_email(user)
        mock_log_error.assert_called_once()
        assert "Ошибка при отправке" in mock_log_error.call_args[0][0]


@patch('app.email_utils.mail.send')
def test_send_email_confirm_token(mock_send, user, app):
    with app.app_context():
        send_email_confirm_token(user)
        assert mock_send.called


@patch('app.email_utils.mail.send', side_effect=Exception("SMTP error"))
@patch('app.email_utils.logging.error')
def test_send_email_confirm_token_exception(mock_log_error, mock_send, user, app):
    with app.app_context():
        send_email_confirm_token(user)
        mock_log_error.assert_called_once()
        assert "Ошибка при отправке" in mock_log_error.call_args[0][0]
