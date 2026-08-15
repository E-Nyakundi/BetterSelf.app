import csv
import json
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.http import HttpResponse, JsonResponse
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.views.generic import ListView, TemplateView

from Accounts.models import Profile
from Finance_Wealth.models import FinancialGoal

from .models import PhoneVerification, Transaction
from .services import (
    DarajaError,
    get_mpesa_analytics,
    get_mpesa_summary,
    initiate_stk_push as _initiate_stk_push,
    normalize_phone_number,
)
from .sms import send_otp_sms


def is_email_verified(user):
    """Firebase owns email verification now (see Accounts.firebase /
    verify_firebase_token), mirrored onto Profile.email_verified —
    true for Google/GitHub sign-ins automatically, and for password
    sign-ups once Firebase confirms the address."""
    return Profile.objects.filter(user=user, email_verified=True).exists()


def get_verified_phone(user):
    """Returns the user's verified PhoneVerification, or None."""
    try:
        pv = user.phone_verification
    except PhoneVerification.DoesNotExist:
        return None
    return pv if pv.is_verified else None


@login_required
@require_POST
def initiate_stk_push(request):
    """4.1.4 — authenticated entry point that creates a PENDING Transaction
    and triggers the Daraja STK push. The callback (separately, and only
    ever server-to-server) is what later resolves it to SUCCESS/FAILED.

    Gated on both a verified email and a verified phone number (matching
    the phone being pushed to) — without this, anyone could spam an
    arbitrary stranger's phone with M-Pesa prompts through this endpoint.
    """
    if not is_email_verified(request.user):
        return JsonResponse(
            {"error": "Please verify your email address before using M-Pesa.", "code": "email_unverified"},
            status=403,
        )

    try:
        body = json.loads(request.body.decode("utf-8")) if request.body else request.POST
    except ValueError:
        return JsonResponse({"error": "Invalid request body."}, status=400)

    phone_number = body.get("phone_number") or body.get("phone")
    amount_raw = body.get("amount")
    financial_goal_id = body.get("financial_goal")

    if not phone_number or not amount_raw:
        return JsonResponse({"error": "phone_number and amount are required."}, status=400)

    verified_phone = get_verified_phone(request.user)
    if verified_phone is None or verified_phone.phone_number != normalize_phone_number(phone_number):
        return JsonResponse(
            {
                "error": "Please verify this phone number before using it for M-Pesa.",
                "code": "phone_unverified",
            },
            status=403,
        )

    try:
        amount = Decimal(str(amount_raw))
        if amount <= 0:
            raise InvalidOperation
    except (InvalidOperation, ValueError):
        return JsonResponse({"error": "amount must be a positive number."}, status=400)

    financial_goal = None
    if financial_goal_id:
        financial_goal = FinancialGoal.objects.filter(
            pk=financial_goal_id, user=request.user
        ).first()
        if financial_goal is None:
            return JsonResponse({"error": "financial_goal not found."}, status=404)

    callback_path = reverse("mpesa-callback")
    if settings.MPESA_CALLBACK_BASE_URL:
        callback_url = f"{settings.MPESA_CALLBACK_BASE_URL.rstrip('/')}{callback_path}"
    else:
        callback_url = request.build_absolute_uri(callback_path)

    try:
        response = _initiate_stk_push(
            phone_number=phone_number,
            amount=amount,
            account_reference=f"LifeApp{request.user.pk}",
            transaction_desc="LifeApp deposit",
            callback_url=callback_url,
        )
    except DarajaError as exc:
        return JsonResponse({"error": str(exc)}, status=502)

    transaction = Transaction.objects.create(
        user=request.user,
        amount=amount,
        phone_number=phone_number,
        checkout_request_id=response.get("CheckoutRequestID"),
        merchant_request_id=response.get("MerchantRequestID"),
        financial_goal=financial_goal,
        status=Transaction.STATUS_PENDING,
    )

    return JsonResponse(
        {
            "transaction_id": transaction.pk,
            "checkout_request_id": transaction.checkout_request_id,
            "status": transaction.status,
            "customer_message": response.get("CustomerMessage"),
        },
        status=201,
    )


class MpesaHubView(LoginRequiredMixin, TemplateView):
    """M-Pesa's own landing page within Finance & Wealth.

    Deliberately a *data* view first: per the brief, this app is "more
    about personal financial data than actually making transactions" --
    so the hub leads with the summary/trend (get_mpesa_summary) and a
    short recent-activity list, with "New deposit" and "Verify phone" as
    secondary calls to action rather than the page's main point.
    """

    template_name = "mpesa/hub.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context["summary"] = get_mpesa_summary(user)
        context["recent_transactions"] = Transaction.objects.filter(user=user)[:5]
        context["email_verified"] = is_email_verified(user)
        context["verified_phone"] = get_verified_phone(user)
        context["goals"] = FinancialGoal.objects.filter(user=user)
        return context


class DepositView(LoginRequiredMixin, TemplateView):
    """The "New deposit" UI -- calls `initiate_stk_push` via fetch().

    Gated the same way the API endpoint is: shows a "verify first" state
    instead of the form when email/phone verification isn't done yet,
    so the form never collects data it can't actually submit.
    """

    template_name = "mpesa/deposit.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context["email_verified"] = is_email_verified(user)
        context["verified_phone"] = get_verified_phone(user)
        context["goals"] = FinancialGoal.objects.filter(user=user)
        preselected_goal = self.request.GET.get("goal")
        context["preselected_goal"] = preselected_goal
        return context


class TransactionListView(LoginRequiredMixin, ListView):
    """4.1.6 — user-scoped, filterable, paginated transaction history."""

    model = Transaction
    template_name = "mpesa/transaction_list.html"
    context_object_name = "transactions"
    paginate_by = 20

    def get_queryset(self):
        qs = Transaction.objects.filter(user=self.request.user)
        status = self.request.GET.get("status")
        financial_goal = self.request.GET.get("financial_goal")
        if status:
            qs = qs.filter(status=status)
        if financial_goal:
            qs = qs.filter(financial_goal_id=financial_goal)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        all_user_transactions = Transaction.objects.filter(user=self.request.user)
        context["status_choices"] = Transaction.STATUS_CHOICES
        context["goals"] = FinancialGoal.objects.filter(user=self.request.user)
        context["selected_status"] = self.request.GET.get("status", "")
        context["selected_goal"] = self.request.GET.get("financial_goal", "")
        context["success_count"] = all_user_transactions.filter(status=Transaction.STATUS_SUCCESS).count()
        context["pending_count"] = all_user_transactions.filter(status=Transaction.STATUS_PENDING).count()
        context["failed_count"] = all_user_transactions.filter(status=Transaction.STATUS_FAILED).count()
        context["total_volume"] = (
            all_user_transactions.filter(status=Transaction.STATUS_SUCCESS)
            .aggregate(total=Sum("amount"))["total"]
            or 0
        )
        import json
        analytics = get_mpesa_analytics(self.request.user)
        context["analytics"] = analytics
        context["analytics_json"] = json.dumps(analytics)
        return context


@login_required
def export_transactions_csv(request):
    """Personal financial data, exportable: same user-scoped filters as
    TransactionListView (status / financial_goal), just unpaginated and
    written out as CSV instead of HTML. Matches the brief's framing of
    this app as being about *data ownership* rather than payments."""
    qs = Transaction.objects.filter(user=request.user)
    status = request.GET.get("status")
    financial_goal = request.GET.get("financial_goal")
    if status:
        qs = qs.filter(status=status)
    if financial_goal:
        qs = qs.filter(financial_goal_id=financial_goal)

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="mpesa_transactions.csv"'
    writer = csv.writer(response)
    writer.writerow(["Date", "Amount (KES)", "Status", "Phone", "Receipt", "Goal"])
    for txn in qs.select_related("financial_goal"):
        writer.writerow([
            txn.created_at.strftime("%Y-%m-%d %H:%M"),
            txn.amount,
            txn.get_status_display(),
            txn.phone_number,
            txn.mpesa_receipt_number or "",
            txn.financial_goal.name if txn.financial_goal else "",
        ])
    return response


class VerifyPageView(LoginRequiredMixin, TemplateView):
    template_name = "mpesa/verify.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["verified_phone"] = get_verified_phone(self.request.user)
        return context


@login_required
def transaction_status(request, pk):
    """Lightweight polling endpoint for the deposit page: lets the UI show
    SUCCESS/FAILED the moment the Daraja callback resolves a PENDING push,
    without a full page reload. Strictly user-scoped, per 4.1.7.
    """
    transaction = Transaction.objects.filter(pk=pk, user=request.user).first()
    if transaction is None:
        return JsonResponse({"error": "Transaction not found."}, status=404)
    return JsonResponse({
        "status": transaction.status,
        "amount": str(transaction.amount),
        "mpesa_receipt_number": transaction.mpesa_receipt_number,
    })


@login_required
def verification_status(request):
    """GET — what the frontend needs to decide which form to show."""
    verified_phone = get_verified_phone(request.user)
    return JsonResponse(
        {
            "email_verified": is_email_verified(request.user),
            "phone_verified": verified_phone is not None,
            "phone_number": verified_phone.phone_number if verified_phone else None,
        }
    )


@login_required
@require_POST
def request_phone_otp(request):
    """Start (or restart) phone verification by sending a 6-digit code."""
    try:
        body = json.loads(request.body.decode("utf-8")) if request.body else request.POST
    except ValueError:
        return JsonResponse({"error": "Invalid request body."}, status=400)

    phone_number = body.get("phone_number") or body.get("phone")
    if not phone_number:
        return JsonResponse({"error": "phone_number is required."}, status=400)
    normalized = normalize_phone_number(phone_number)

    pv, _ = PhoneVerification.objects.get_or_create(user=request.user, defaults={"phone_number": normalized})
    if not pv.can_resend():
        return JsonResponse(
            {"error": "Please wait before requesting another code.", "code": "cooldown"},
            status=429,
        )

    code = pv.issue_otp(normalized)
    sent = send_otp_sms(normalized, code)

    response_data = {"message": "Verification code sent.", "phone_number": normalized}
    if settings.DEBUG and getattr(settings, "SMS_BACKEND", "console") == "console":
        # No real SMS provider configured -- surface the code directly so
        # the verification flow is testable end-to-end in development.
        response_data["debug_code"] = code
        response_data["debug_note"] = "SMS_BACKEND=console: no real SMS was sent."
    elif not sent:
        response_data["warning"] = "We couldn't confirm the SMS was sent. Try again if it doesn't arrive."

    return JsonResponse(response_data)


@login_required
@require_POST
def verify_phone_otp(request):
    try:
        body = json.loads(request.body.decode("utf-8")) if request.body else request.POST
    except ValueError:
        return JsonResponse({"error": "Invalid request body."}, status=400)

    code = body.get("code") or body.get("otp")
    if not code:
        return JsonResponse({"error": "code is required."}, status=400)

    try:
        pv = request.user.phone_verification
    except PhoneVerification.DoesNotExist:
        return JsonResponse({"error": "Request a verification code first."}, status=400)

    success, error = pv.verify(code)
    if not success:
        return JsonResponse({"error": error}, status=400)
    return JsonResponse({"message": "Phone number verified.", "phone_number": pv.phone_number})