"""Daraja STK Push callback (webhook) handling.

Per 4.1.3 / 4.1.7: never trusts the frontend, matches purely on
CheckoutRequestID, stores the full raw payload regardless of outcome, and
is idempotent — replays of an already-resolved transaction are accepted
(200 OK) but do not mutate state twice.
"""
import json
import logging

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import Transaction

logger = logging.getLogger(__name__)


def _extract_metadata(callback_metadata):
    """Flatten Daraja's {"Item": [{"Name": .., "Value": ..}, ...]} shape."""
    items = (callback_metadata or {}).get("Item", [])
    return {item.get("Name"): item.get("Value") for item in items}


@csrf_exempt
@require_POST
def stk_callback(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        logger.warning("Received unparsable M-Pesa callback body")
        # Still 200: Daraja retries on non-2xx, and a malformed body isn't
        # something a retry will fix.
        return JsonResponse({"ResultCode": 0, "ResultDesc": "Accepted"})

    stk_callback_data = payload.get("Body", {}).get("stkCallback", {})
    checkout_request_id = stk_callback_data.get("CheckoutRequestID")

    if not checkout_request_id:
        logger.warning("M-Pesa callback missing CheckoutRequestID: %s", payload)
        return JsonResponse({"ResultCode": 0, "ResultDesc": "Accepted"})

    try:
        transaction = Transaction.objects.get(checkout_request_id=checkout_request_id)
    except Transaction.DoesNotExist:
        logger.warning("M-Pesa callback for unknown CheckoutRequestID: %s", checkout_request_id)
        return JsonResponse({"ResultCode": 0, "ResultDesc": "Accepted"})

    # Idempotency: a transaction that already left PENDING is final.
    # Accept the replay without touching it again.
    if transaction.status != Transaction.STATUS_PENDING:
        return JsonResponse({"ResultCode": 0, "ResultDesc": "Accepted"})

    result_code = stk_callback_data.get("ResultCode")
    transaction.merchant_request_id = stk_callback_data.get("MerchantRequestID") or transaction.merchant_request_id

    if result_code == 0:
        metadata = _extract_metadata(stk_callback_data.get("CallbackMetadata"))
        transaction.mark_success(
            mpesa_receipt_number=metadata.get("MpesaReceiptNumber", ""),
            raw_payload=payload,
        )
    else:
        transaction.mark_failed(raw_payload=payload)

    return JsonResponse({"ResultCode": 0, "ResultDesc": "Accepted"})
