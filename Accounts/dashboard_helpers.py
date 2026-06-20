"""
Data helpers for Accounts.views.DashboardView.

Split out of views.py (rather than inlined) because each function maps
1:1 to a dashboard card, and the Roadmap's Phase 1 acceptance check is
"every number on the dashboard traces to an actual query, no hardcoded
placeholder data anywhere in the template" — keeping each card's query in
its own named function makes that easy to audit card-by-card.
"""
from datetime import datetime, time, timedelta

from django.utils import timezone

from Time_Manager.models import DailyGoal, Goals, Routine
from Time_Manager.utils import build_schedule_for_date
from WellBeing.models import JournalEntry
from Inventory.models import Item
from Finance_Wealth.models import FinancialGoal
from mpesa.services import get_mpesa_summary


# ---------------------------------------------------------------------------
# Next Up
# ---------------------------------------------------------------------------

def get_next_up(user, today, now_time, limit=3):
    """Today's remaining schedule (goals + routines), soonest first.

    Reuses Time_Manager's build_schedule_for_date so this card and the
    full Schedule page can never disagree about what's on today.
    """
    full_schedule = build_schedule_for_date(user, today)
    upcoming = [item for item in full_schedule if item['start_time'] >= now_time]
    return upcoming[:limit]


# ---------------------------------------------------------------------------
# Today's Focus
# ---------------------------------------------------------------------------

def get_today_focus(user, today, limit=8):
    """Today's DailyGoal tasks, incomplete first, for the checklist card."""
    goals = DailyGoal.objects.filter(
        date=today,
        day_goal__weekly_goal__monthly_goal__yearly_goal__goals__user=user,
    ).order_by('completed', 'start_time')[:limit]
    return goals


# ---------------------------------------------------------------------------
# Active Streaks
# ---------------------------------------------------------------------------

def get_active_streaks(user, today, limit=3):
    """Top current streaks across the user's top-level Goals.

    See Goals.current_streak() for the definition. Goals with a streak of
    0 (no history, or streak broken) are excluded — the card shows an
    honest empty state rather than a row full of zeros.
    """
    goals = Goals.objects.filter(user=user)
    streaks = []
    for goal in goals:
        streak = goal.current_streak(reference_date=today)
        if streak > 0:
            streaks.append({'name': goal.name, 'streak': streak})
    streaks.sort(key=lambda row: row['streak'], reverse=True)
    return streaks[:limit]


# ---------------------------------------------------------------------------
# Goal Progress
# ---------------------------------------------------------------------------

def get_goal_progress(user, limit=4):
    """Top-level goals with a real % complete, for the Goals card.

    progress_percentage() returns None when a goal has no DailyGoal
    leaves yet — that's filtered to a separate bucket so the template can
    say "not started" instead of drawing a 0% bar.
    """
    goals = Goals.objects.filter(user=user).order_by('-created_at')
    rows = []
    for goal in goals[:limit]:
        pct = goal.progress_percentage()
        rows.append({'name': goal.name, 'pct': pct, 'id': goal.id})
    return rows


# ---------------------------------------------------------------------------
# Energy & Wellbeing
# ---------------------------------------------------------------------------

def get_wellbeing_rings(user, today, lookback_days=7):
    """Average mood/energy/focus over the last N days, as 0-100 ring %.

    Returns None for a metric entirely if there's no data in the window
    (rather than a fake 0%), so the template can fall back to a
    "no entries yet" message per-metric if needed.
    """
    window_start = today - timedelta(days=lookback_days - 1)
    entries = JournalEntry.objects.filter(user=user, days_date__gte=window_start, days_date__lte=today)

    def avg_to_pct(field_name):
        values = [getattr(e, field_name) for e in entries if getattr(e, field_name) is not None]
        if not values:
            return None
        avg = sum(values) / len(values)
        return round(avg / 5 * 100)

    return {
        'energy': avg_to_pct('energy'),
        'mood': avg_to_pct('mood'),
        'focus': avg_to_pct('focus'),
        'has_any_entries': entries.exists(),
    }


# ---------------------------------------------------------------------------
# Recent Activity
# ---------------------------------------------------------------------------

def _to_aware_datetime(d, t=None):
    if d is None:
        return None
    combined = datetime.combine(d, t or time.min)
    if timezone.is_naive(combined):
        return timezone.make_aware(combined, timezone.get_default_timezone())
    return combined


def get_recent_activity(user, limit=8):
    """Unified recent-activity feed: goal completions + journal entries +
    inventory additions, merged and sorted by timestamp.

    Data-quality note: DailyGoal and JournalEntry don't store a true
    "completed/created at" timestamp, only a scheduled/logged date (plus
    time-of-day for journal entries). We use those as the best available
    proxy for recency — Item.created_at is the only field here that's a
    real timestamp. This is the same tradeoff the roadmap calls out:
    "cheapest real version... no new model required."
    """
    activities = []

    completed_goals = DailyGoal.objects.filter(
        day_goal__weekly_goal__monthly_goal__yearly_goal__goals__user=user,
        completed=True,
        date__isnull=False,
    ).order_by('-date', '-start_time')[:limit]
    for g in completed_goals:
        activities.append({
            'icon': 'fa-check',
            'text': f'Completed "{g.goal}"',
            'timestamp': _to_aware_datetime(g.date, g.start_time),
        })

    journal_entries = JournalEntry.objects.filter(user=user).order_by('-days_date', '-time_of_day')[:limit]
    for j in journal_entries:
        activities.append({
            'icon': 'fa-book',
            'text': 'Wrote a journal entry',
            'timestamp': _to_aware_datetime(j.days_date, j.time_of_day),
        })

    items = Item.objects.filter(user=user).order_by('-created_at')[:limit]
    for i in items:
        activities.append({
            'icon': 'fa-box',
            'text': f'Added "{i.name}" to inventory',
            'timestamp': i.created_at,
        })

    activities = [a for a in activities if a['timestamp'] is not None]
    activities.sort(key=lambda a: a['timestamp'], reverse=True)

    now = timezone.now()
    for a in activities[:limit]:
        a['time_ago'] = _humanize_delta(now - a['timestamp'])

    return activities[:limit]


def _humanize_delta(delta):
    seconds = delta.total_seconds()
    if seconds < 60:
        return "Just now"
    minutes = int(seconds // 60)
    if minutes < 60:
        return f"{minutes}m ago"
    hours = int(minutes // 60)
    if hours < 24:
        return f"{hours}h ago"
    days = int(hours // 24)
    if days == 1:
        return "Yesterday"
    if days < 7:
        return f"{days}d ago"
    weeks = int(days // 7)
    return f"{weeks}w ago"


# ---------------------------------------------------------------------------
# Financial Snapshot (Phase 4.0)
# ---------------------------------------------------------------------------

def get_finance_summary(user, limit=3):
    """Compact Finance card summary: total saved / total target across all
    FinancialGoals, plus the top few goals by progress, plus a one-line
    M-Pesa data mention (this card stays goal-centric; full M-Pesa data
    lives in its own app, linked from the card).

    Phase 4.0 scope only — these are manually-entered goal targets, not
    real transaction data, so this is a snapshot of *targets*, not actual
    account balances. Returns has_any_goals=False when the user hasn't
    created one yet, so the template can show the honest "add your first
    goal" state instead of a 0/0 figure.
    """
    goals = FinancialGoal.objects.filter(user=user)
    mpesa_summary = get_mpesa_summary(user)
    if not goals.exists():
        return {'has_any_goals': False, 'mpesa': mpesa_summary}

    total_target = sum(g.target_amount for g in goals)
    total_saved = sum(g.current_amount for g in goals)
    overall_pct = round(float(total_saved) / float(total_target) * 100) if total_target else None

    top_goals = sorted(
        goals,
        key=lambda g: (g.progress_percentage() if g.progress_percentage() is not None else -1),
        reverse=True,
    )[:limit]

    return {
        'has_any_goals': True,
        'total_target': total_target,
        'total_saved': total_saved,
        'overall_pct': overall_pct,
        'top_goals': [{'name': g.name, 'pct': g.progress_percentage()} for g in top_goals],
        'mpesa': mpesa_summary,
    }