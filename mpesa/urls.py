from django.urls import path

from .callbacks import stk_callback
from .views import (
    DepositView,
    MpesaHubView,
    TransactionListView,
    VerifyPageView,
    export_transactions_csv,
    initiate_stk_push,
    request_phone_otp,
    transaction_status,
    verification_status,
    verify_phone_otp,
)

urlpatterns = [
    path("", MpesaHubView.as_view(), name="mpesa-hub"),
    path("deposit/", DepositView.as_view(), name="mpesa-deposit-page"),
    path("initiate/", initiate_stk_push, name="mpesa-initiate"),
    path("callback/", stk_callback, name="mpesa-callback"),
    path("transactions/", TransactionListView.as_view(), name="mpesa-transaction-list"),
    path("transactions/export/", export_transactions_csv, name="mpesa-transaction-export"),
    path("transactions/<int:pk>/status/", transaction_status, name="mpesa-transaction-status"),
    path("verify/", VerifyPageView.as_view(), name="mpesa-verify-page"),
    path("verification/status/", verification_status, name="mpesa-verification-status"),
    path("verification/phone/request/", request_phone_otp, name="mpesa-phone-otp-request"),
    path("verification/phone/verify/", verify_phone_otp, name="mpesa-phone-otp-verify"),
]