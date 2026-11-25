from azure.communication.sms import SmsClient
from azure.core.exceptions import AzureError

from backend.auth.config import get_auth_settings


class SmsNotConfigured(RuntimeError):
    pass


class SmsDeliveryError(RuntimeError):
    pass


def is_sms_configured() -> bool:
    settings = get_auth_settings()
    return bool(settings.sms_connection_string and settings.sms_sender)


def send_verification_code(phone_number: str, code: str, purpose: str) -> None:
    settings = get_auth_settings()
    if not settings.sms_connection_string or not settings.sms_sender:
        raise SmsNotConfigured("SMS delivery is not configured.")

    message = (
        f"Your Smart Stadium verification code is {code}. "
        "It expires in 5 minutes."
    )

    try:
        client = SmsClient.from_connection_string(
            settings.sms_connection_string
        )
        results = client.send(
            from_=settings.sms_sender,
            to=[phone_number],
            message=message,
            tag=f"smart-stadium-{purpose}",
        )
    except AzureError as error:
        raise SmsDeliveryError("SMS provider delivery failed.") from error

    if not results or any(not result.successful for result in results):
        raise SmsDeliveryError("SMS provider did not accept the message.")
