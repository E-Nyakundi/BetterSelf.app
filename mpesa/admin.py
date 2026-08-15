from django.contrib import admin
from .models import PhoneVerification, Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        "id", "user", "amount", "phone_number", "status",
        "mpesa_receipt_number", "financial_goal", "created_at",
    )
    list_filter = ("status", "direction")
    search_fields = ("phone_number", "checkout_request_id", "mpesa_receipt_number", "user__username")
    readonly_fields = ("checkout_request_id", "merchant_request_id", "raw_callback_payload", "created_at", "updated_at")


@admin.register(PhoneVerification)
class PhoneVerificationAdmin(admin.ModelAdmin):
    list_display = ("user", "phone_number", "is_verified", "otp_attempts", "updated_at")
    list_filter = ("is_verified",)
    search_fields = ("phone_number", "user__username")
    readonly_fields = ("otp_hash", "otp_expires_at", "otp_attempts", "otp_last_sent_at", "created_at", "updated_at")