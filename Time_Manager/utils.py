from datetime import datetime, timedelta
from django.utils.dateparse import parse_datetime
from django.utils import timezone


def build_schedule_for_date(user, target_date):
    """Build the combined goal+routine schedule for a single day.

    Shared by Time_Manager.views.ScheduleView and Accounts' dashboard "Next
    Up" card so the two views can't drift out of sync. Returns a list of
    dicts sorted by start_time, with simple overlap annotation, exactly as
    ScheduleView used to build it inline.
    """
    from .models import DailyGoal, Routine

    goals = DailyGoal.objects.filter(
        date=target_date,
        day_goal__weekly_goal__monthly_goal__yearly_goal__goals__user=user,
    ).select_related(
        'day_goal__weekly_goal__monthly_goal__yearly_goal__goals'
    )

    is_weekend = target_date.weekday() >= 5
    routines = Routine.objects.filter(user=user, is_weekend=is_weekend, is_split=False)

    schedule = []

    for goal in goals:
        if not (goal.start_time and goal.end_time):
            continue
        schedule.append({
            'start_time': goal.start_time,
            'end_time': goal.end_time,
            'time': f"{goal.start_time.strftime('%I:%M %p')} - {goal.end_time.strftime('%I:%M %p')}",
            'activity': goal.goal,
            'type': 'goal',
            'completed': goal.completed,
            'goal_id': goal.id,
        })

    for routine in routines:
        schedule.append({
            'start_time': routine.start_time,
            'end_time': routine.end_time,
            'time': f"{routine.start_time.strftime('%I:%M %p')} - {routine.end_time.strftime('%I:%M %p')}",
            'activity': routine.name,
            'type': 'routine',
            'completed': None,
            'goal_id': None,
        })

    schedule.sort(key=lambda x: x['start_time'])

    for i in range(len(schedule) - 1):
        current = schedule[i]
        next_activity = schedule[i + 1]
        if current['end_time'] > next_activity['start_time']:
            current['activity'] += f" (Overlaps with {next_activity['activity']})"

    return schedule

def create_events_for_routine(routine):
    from .models import Event
    days = [0, 1, 2, 3, 4]  # Weekdays by default
    if routine.is_weekend:
        days = [5, 6]  # Saturday and Sunday

    for day in days:
        today = datetime.today()
        next_date = today + timedelta((day - today.weekday()) % 7)

        # Ensure start_time and end_time are datetime.time objects
        if isinstance(routine.start_time, str):
            start_time = datetime.strptime(routine.start_time, "%H:%M:%S").time()
        else:
            start_time = routine.start_time

        if isinstance(routine.end_time, str):
            end_time = datetime.strptime(routine.end_time, "%H:%M:%S").time()
        else:
            end_time = routine.end_time

        # Combine the date and time correctly
        start_datetime = timezone.make_aware(datetime.combine(next_date, start_time))
        end_datetime = timezone.make_aware(datetime.combine(next_date, end_time))

        event, _ = Event.objects.update_or_create(
            routine=routine,
            start_datetime__date=next_date.date(),
            defaults={
                'user': routine.user,
                'title': routine.name,
                'description': routine.instruction,
                'start_datetime': start_datetime,
                'end_datetime': end_datetime,
                'is_recurring': True,
            },
        )
        
def create_event_for_daily_goal(daily_goal):
    from .models import Event
    start_time = daily_goal.start_time
    end_time = daily_goal.end_time
    date = daily_goal.date  # Assuming date is already a DateField in DailyGoal

    if not (date and start_time and end_time):
        return None

    start_datetime = timezone.make_aware(timezone.datetime.combine(date, start_time))
    end_datetime = timezone.make_aware(timezone.datetime.combine(date, end_time))
    user = None
    if daily_goal.day_goal_id:
        try:
            user = daily_goal.day_goal.weekly_goal.monthly_goal.yearly_goal.goals.user
        except AttributeError:
            user = None

    event, _ = Event.objects.update_or_create(
        goal=daily_goal,
        defaults={
            'user': user,
            'title': daily_goal.goal or '',
            'description': daily_goal.description,
            'start_datetime': start_datetime,
            'start_time': start_time,
            'end_datetime': end_datetime,
            'end_time': end_time,
        },
    )

    return event
