"""SMS delivery for phone-verification OTPs (mpesa/models.PhoneVerification).

Mirrors the EMAIL_BACKEND pattern already used in settings.py: a small
backend abstraction so phone verification works out of the box in
development (console backend, zero credentials needed) and can be
pointed at a real gateway in production via the SMS_BACKEND env var.
Default real-provider wiring is for Africa's Talking, the most common
SMS gateway for Kenyan apps -- no secrets hardcoded, same as MPESA_*.

`send_otp_sms` deliberately never raises: a misconfigured or unreachable
SMS provider should degrade (logged, reported back as `False`) rather
than 500 the whole verification flow.
"""
import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def _send_console(phone_number, message):
    """Dev-friendly default: the OTP is logged, not actually sent.

    request_phone_otp() also echoes the code back in the JSON response
    when DEBUG + this backend is active, so the verification flow is
    fully testable without any SMS provider configured.
    """
    logger.info("[SMS:console] to=%s message=%s", phone_number, message)
    return True


def _send_africastalking(phone_number, message):
    api_key = getattr(settings, "AFRICASTALKING_API_KEY", None)
    username = getattr(settings, "AFRICASTALKING_USERNAME", None)
    if not api_key or not username:
        logger.warning(
            "SMS_BACKEND=africastalking but AFRICASTALKING_API_KEY/USERNAME "
            "are not configured; falling back to the console backend."
        )
        return _send_console(phone_number, message)

    to_number = phone_number if phone_number.startswith("+") else f"+{phone_number}"
    payload = {"username": username, "to": to_number, "message": message}
    sender_id = getattr(settings, "AFRICASTALKING_SENDER_ID", "")
    if sender_id:
        payload["from"] = sender_id

    try:
        response = requests.post(
            "https://api.africastalking.com/version1/messaging",
            headers={
                "apiKey": api_key,
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
            },
            data=payload,
            timeout=15,
        )
    except requests.RequestException:
        logger.exception("Africa's Talking SMS request raised an exception")
        return False

    if response.status_code not in (200, 201):
        logger.error("Africa's Talking SMS send failed (%s): %s", response.status_code, response.text)
        return False
    return True


_BACKENDS = {
    "console": _send_console,
    "africastalking": _send_africastalking,
}


def send_otp_sms(phone_number, code):
    """Send a 6-digit verification code to `phone_number`. Returns bool success.

    Never raises -- a flaky/unconfigured provider degrades to a `False`
    return (caller can surface "couldn't send, try again"), not a 500.
    """
    message = f"Your LifeApp verification code is {code}. It expires in 10 minutes."
    backend_name = getattr(settings, "SMS_BACKEND", "console")
    backend = _BACKENDS.get(backend_name, _send_console)
    try:
        return backend(phone_number, message)
    except Exception:
        logger.exception("send_otp_sms backend '%s' raised unexpectedly", backend_name)
        return False