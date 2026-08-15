import secrets

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.db import models
from django.utils import timezone


class Transaction(models.Model):
    """M-Pesa STK Push transaction ledger entry.

    Deliberately separate from `Finance_Wealth.FinancialGoal` (per roadmap
    4.1.1) — this is the raw, audit-grade record of money movement.
    Reconciling transactions into goal progress is Phase 4.4's job, not
    this model's.
    """

    DIRECTION_IN = "IN"
    DIRECTION_OUT = "OUT"
    DIRECTION_CHOICES = [
        (DIRECTION_IN, "In"),
        (DIRECTION_OUT, "Out"),
    ]

    STATUS_PENDING = "PENDING"
    STATUS_SUCCESS = "SUCCESS"
    STATUS_FAILED = "FAILED"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_SUCCESS, "Success"),
        (STATUS_FAILED, "Failed"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="mpesa_transactions",
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    phone_number = models.CharField(max_length=15)
    direction = models.CharField(
        max_length=3, choices=DIRECTION_CHOICES, null=True, blank=True
    )

    checkout_request_id = models.CharField(max_length=100, unique=True)
    merchant_request_id = models.CharField(max_length=100, null=True, blank=True)
    mpesa_receipt_number = models.CharField(max_length=50, null=True, blank=True)

    raw_callback_payload = models.JSONField(null=True, blank=True)

    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING
    )

    financial_goal = models.ForeignKey(
        "Finance_Wealth.FinancialGoal",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="mpesa_transactions",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.phone_number} - {self.amount} ({self.status})"

    def mark_success(self, *, mpesa_receipt_number, raw_payload):
        self.status = self.STATUS_SUCCESS
        self.mpesa_receipt_number = mpesa_receipt_number
        self.raw_callback_payload = raw_payload
        self.save(update_fields=["status", "mpesa_receipt_number", "raw_callback_payload", "updated_at"])

    def mark_failed(self, *, raw_payload):
        self.status = self.STATUS_FAILED
        self.raw_callback_payload = raw_payload
        self.save(update_fields=["status", "raw_callback_payload", "updated_at"])


class PhoneVerification(models.Model):
    """Proof that `user` controls `phone_number`, required before that
    number can be used in an STK push (see views.initiate_stk_push).

    Deliberately separate from Profile / Firebase's email-verification
    claim — this is
    specifically the app's trust in a phone number for *payments*, not a
    general contact field.
    """

    OTP_TTL_MINUTES = 10
    OTP_RESEND_COOLDOWN_SECONDS = 60
    OTP_MAX_ATTEMPTS = 5

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="phone_verification",
    )
    phone_number = models.CharField(max_length=15)
    is_verified = models.BooleanField(default=False)

    otp_hash = models.CharField(max_length=128, blank=True)
    otp_expires_at = models.DateTimeField(null=True, blank=True)
    otp_attempts = models.PositiveSmallIntegerField(default=0)
    otp_last_sent_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user} - {self.phone_number} ({'verified' if self.is_verified else 'unverified'})"

    def can_resend(self):
        if not self.otp_last_sent_at:
            return True
        elapsed = (timezone.now() - self.otp_last_sent_at).total_seconds()
        return elapsed >= self.OTP_RESEND_COOLDOWN_SECONDS

    def issue_otp(self, phone_number):
        """(Re)start verification for a (possibly new) phone number.
        Returns the plaintext code so the caller can send it — only the
        hash is persisted.
        """
        code = f"{secrets.randbelow(1_000_000):06d}"
        self.phone_number = phone_number
        self.is_verified = False
        self.otp_hash = make_password(code)
        self.otp_expires_at = timezone.now() + timezone.timedelta(minutes=self.OTP_TTL_MINUTES)
        self.otp_attempts = 0
        self.otp_last_sent_at = timezone.now()
        self.save()
        return code

    def verify(self, code):
        """Returns (success, error_message). Locks out after too many
        wrong attempts — 6-digit codes are a small enough space that
        unlimited guessing would matter.
        """
        if self.is_verified:
            return True, None
        if not self.otp_hash or not self.otp_expires_at:
            return False, "No verification in progress. Request a code first."
        if timezone.now() > self.otp_expires_at:
            return False, "Code expired. Request a new one."
        if self.otp_attempts >= self.OTP_MAX_ATTEMPTS:
            return False, "Too many incorrect attempts. Request a new code."

        if check_password(code, self.otp_hash):
            self.is_verified = True
            self.otp_hash = ""
            self.otp_expires_at = None
            self.otp_attempts = 0
            self.save()
            return True, None

        self.otp_attempts += 1
        self.save(update_fields=["otp_attempts", "updated_at"])
        return False, "Incorrect code."