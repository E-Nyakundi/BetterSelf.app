"""Daraja (Safaricom M-Pesa) sandbox API client.

Covers 4.1.2 — OAuth token generation, STK Push ("M-Pesa Express") request
building, and password/timestamp generation. No secrets live here; all
credentials come from environment variables (see settings.py / .env).

Also home to `get_mpesa_summary()` — a read-only aggregate over a user's
`Transaction` ledger. Per the roadmap, this app is "more about personal
financial data than actually making transactions": the hub page and the
Finance & Wealth dashboard's M-Pesa section both call this rather than
duplicating aggregation logic.
"""
import base64
import datetime
from datetime import timedelta

import requests
from django.conf import settings
from django.db.models import Sum
from django.db.models.functions import TruncDate
from django.utils import timezone


class DarajaError(Exception):
    """Raised when a Daraja API call fails or returns an error payload."""


def _format_day_label(day):
    """Format a date as e.g. '9 Jun' without a leading zero on the day.

    `%-d` (no leading zero) is a glibc/macOS strftime extension and raises
    `ValueError: Invalid format string` on Windows. `%#d` is the Windows
    equivalent. Rather than branch on platform, just build the label
    manually so it works the same everywhere.
    """
    return f"{day.day} {day.strftime('%b')}"


def _base_url():
    return settings.MPESA_BASE_URL.rstrip("/")


def get_access_token():
    """OAuth token generation against Daraja's /oauth endpoint.

    Tokens are short-lived (~1hr per Daraja docs); callers should fetch a
    fresh token per request rather than caching across processes for now.
    Optimizing this is a Phase 7 concern, not 4.1's.
    """
    consumer_key = settings.MPESA_CONSUMER_KEY
    consumer_secret = settings.MPESA_CONSUMER_SECRET
    if not consumer_key or not consumer_secret:
        raise DarajaError("MPESA_CONSUMER_KEY / MPESA_CONSUMER_SECRET are not configured.")

    url = f"{_base_url()}/oauth/v1/generate?grant_type=client_credentials"
    response = requests.get(url, auth=(consumer_key, consumer_secret), timeout=30)
    if response.status_code != 200:
        raise DarajaError(f"OAuth token request failed ({response.status_code}): {response.text}")

    data = response.json()
    token = data.get("access_token")
    if not token:
        raise DarajaError(f"OAuth response missing access_token: {data}")
    return token


def _generate_timestamp():
    return datetime.datetime.now().strftime("%Y%m%d%H%M%S")


def _generate_password(shortcode, passkey, timestamp):
    raw = f"{shortcode}{passkey}{timestamp}"
    return base64.b64encode(raw.encode("utf-8")).decode("utf-8")


def normalize_phone_number(phone_number):
    """Coerce common Kenyan phone formats into Daraja's expected 2547XXXXXXXX."""
    digits = "".join(ch for ch in phone_number if ch.isdigit())
    if digits.startswith("0") and len(digits) == 10:
        digits = "254" + digits[1:]
    elif digits.startswith("7") and len(digits) == 9:
        digits = "254" + digits
    elif digits.startswith("254"):
        pass
    return digits


def initiate_stk_push(*, phone_number, amount, account_reference, transaction_desc, callback_url):
    """Build and send an STK Push ("M-Pesa Express") request.

    Returns the parsed JSON response from Daraja, which includes
    CheckoutRequestID / MerchantRequestID on success.
    """
    shortcode = settings.MPESA_SHORTCODE
    passkey = settings.MPESA_PASSKEY
    if not shortcode or not passkey:
        raise DarajaError("MPESA_SHORTCODE / MPESA_PASSKEY are not configured.")

    token = get_access_token()
    timestamp = _generate_timestamp()
    password = _generate_password(shortcode, passkey, timestamp)
    phone = normalize_phone_number(phone_number)

    payload = {
        "BusinessShortCode": shortcode,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": int(amount),
        "PartyA": phone,
        "PartyB": shortcode,
        "PhoneNumber": phone,
        "CallBackURL": callback_url,
        "AccountReference": account_reference[:12],
        "TransactionDesc": transaction_desc[:13],
    }

    url = f"{_base_url()}/mpesa/stkpush/v1/processrequest"
    response = requests.post(
        url,
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    data = response.json()
    if response.status_code != 200 or data.get("ResponseCode") not in (None, "0"):
        raise DarajaError(f"STK push request failed: {data}")
    return data


def get_mpesa_summary(user, trend_days=14):
    """Read-only aggregate over `user`'s Transaction ledger.

    Returns a dict the templates can render directly:
    - has_activity: False short-circuits everything else (honest empty
      state, same convention as Goals/FinancialGoal progress methods).
    - total_deposited: sum of SUCCESS amounts only — pending/failed money
      never moved, so it shouldn't count toward a "deposited" figure.
    - success_rate: percentage of all attempts that resolved SUCCESS.
    - trend: last `trend_days` days of successful-deposit totals, for a
      simple CSS bar chart — no charting library, same approach the
      project already uses for `bs-ring`.
    """
    # Local import avoids a module-load-time circular import with .models.
    from .models import Transaction

    qs = Transaction.objects.filter(user=user)
    total_count = qs.count()

    today = timezone.localdate()
    if total_count == 0:
        empty_trend = [
            {"label": (today - timedelta(days=i)).strftime("%a")[0], "date": (today - timedelta(days=i)).isoformat(), "amount": 0, "pct": 0}
            for i in range(trend_days - 1, -1, -1)
        ]
        return {
            "has_activity": False,
            "total_count": 0,
            "trend": empty_trend,
        }

    success_qs = qs.filter(status=Transaction.STATUS_SUCCESS)
    success_count = success_qs.count()
    pending_count = qs.filter(status=Transaction.STATUS_PENDING).count()
    failed_count = qs.filter(status=Transaction.STATUS_FAILED).count()
    total_deposited = success_qs.aggregate(total=Sum("amount"))["total"] or 0
    success_rate = round((success_count / total_count) * 100) if total_count else None
    last_transaction = qs.first()  # Transaction.Meta.ordering = ['-created_at']

    since = timezone.now() - timedelta(days=trend_days - 1)
    daily_totals = (
        success_qs.filter(created_at__gte=since)
        .annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(total=Sum("amount"))
    )
    totals_by_day = {row["day"]: row["total"] for row in daily_totals}
    max_amount = max(totals_by_day.values()) if totals_by_day else 0

    trend = []
    for i in range(trend_days - 1, -1, -1):
        day = today - timedelta(days=i)
        amount = totals_by_day.get(day, 0)
        pct = round((float(amount) / float(max_amount)) * 100) if max_amount else 0
        trend.append({
            "label": day.strftime("%a")[0],
            "date": day.isoformat(),
            "amount": amount,
            "pct": pct,
        })

    return {
        "has_activity": True,
        "total_count": total_count,
        "success_count": success_count,
        "pending_count": pending_count,
        "failed_count": failed_count,
        "total_deposited": total_deposited,
        "success_rate": success_rate,
        "last_transaction": last_transaction,
        "trend": trend,
    }

def get_mpesa_analytics(user):
    """Extended analytics for the transaction history page.

    Returns monthly aggregates, category breakdown by goal, and a
    30-day daily trend — all the data the chart-heavy transaction
    history page needs without scattering queries across the view.
    """
    from .models import Transaction
    from django.db.models import Count
    from django.db.models.functions import TruncMonth
    import datetime

    qs = Transaction.objects.filter(user=user)
    success_qs = qs.filter(status=Transaction.STATUS_SUCCESS)

    today = timezone.localdate()

    # 30-day daily trend
    since_30 = timezone.now() - timedelta(days=29)
    daily_raw = (
        success_qs.filter(created_at__gte=since_30)
        .annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(total=Sum("amount"), count=Count("id"))
        .order_by("day")
    )
    daily_by_date = {row["day"]: {"amount": float(row["total"]), "count": row["count"]} for row in daily_raw}
    daily_trend = []
    for i in range(29, -1, -1):
        day = today - timedelta(days=i)
        d = daily_by_date.get(day, {"amount": 0, "count": 0})
        daily_trend.append({
            "date": day.isoformat(),
            "label": _format_day_label(day),
            "amount": d["amount"],
            "count": d["count"],
        })

    # Monthly aggregates (last 6 months)
    since_6mo = timezone.now() - timedelta(days=180)
    monthly_raw = (
        success_qs.filter(created_at__gte=since_6mo)
        .annotate(month=TruncMonth("created_at"))
        .values("month")
        .annotate(total=Sum("amount"), count=Count("id"))
        .order_by("month")
    )
    monthly = [
        {
            "label": row["month"].strftime("%b %Y"),
            "amount": float(row["total"]),
            "count": row["count"],
        }
        for row in monthly_raw
    ]

    # Goal breakdown (how much funded toward each goal)
    goal_breakdown_raw = (
        success_qs.filter(financial_goal__isnull=False)
        .values("financial_goal__name")
        .annotate(total=Sum("amount"), count=Count("id"))
        .order_by("-total")[:6]
    )
    unallocated = float(
        success_qs.filter(financial_goal__isnull=True)
        .aggregate(total=Sum("amount"))["total"] or 0
    )
    goal_breakdown = [
        {"name": row["financial_goal__name"], "amount": float(row["total"]), "count": row["count"]}
        for row in goal_breakdown_raw
    ]
    if unallocated > 0:
        goal_breakdown.append({"name": "Unallocated", "amount": unallocated, "count": None})

    # Overall stats
    total_success = float(success_qs.aggregate(t=Sum("amount"))["t"] or 0)
    avg_transaction = total_success / success_qs.count() if success_qs.count() else 0

    # This month vs last month
    first_this_month = today.replace(day=1)
    first_last_month = (first_this_month - timedelta(days=1)).replace(day=1)
    this_month_total = float(
        success_qs.filter(created_at__date__gte=first_this_month)
        .aggregate(t=Sum("amount"))["t"] or 0
    )
    last_month_total = float(
        success_qs.filter(
            created_at__date__gte=first_last_month,
            created_at__date__lt=first_this_month,
        )
        .aggregate(t=Sum("amount"))["t"] or 0
    )
    mom_change = None
    if last_month_total > 0:
        mom_change = round(((this_month_total - last_month_total) / last_month_total) * 100, 1)

    return {
        "daily_trend": daily_trend,
        "monthly": monthly,
        "goal_breakdown": goal_breakdown,
        "this_month_total": this_month_total,
        "last_month_total": last_month_total,
        "mom_change": mom_change,
        "avg_transaction": avg_transaction,
        "total_success": total_success,
    }
