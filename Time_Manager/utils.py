from datetime import datetime, timedelta
from django.utils.dateparse import parse_datetime
from django.utils import timezone

def create_events_for_routine(routine):
    from .models import Event, Routine
    days = [0, 1, 2, 3, 4]  # Weekdays (Monday=0, Friday=4) by default
    if routine.is_weekend:
        days = [5, 6]  # Saturday and Sunday

    for day in days:
        today = datetime.today()
        next_date = today + timedelta((day - today.weekday()) % 7)

        start_datetime_str = routine.start_time.isoformat()  # Assuming routine.start_time is a datetime.time object
        end_datetime_str = routine.end_time.isoformat()  # Assuming routine.end_time is a datetime.time object

        start_datetime = parse_datetime(start_datetime_str)
        end_datetime = parse_datetime(end_datetime_str)
        
        if not start_datetime:
            start_datetime = timezone.make_aware(datetime.combine(next_date, routine.start_time))

        if not end_datetime:
            end_datetime = timezone.make_aware(datetime.combine(next_date, routine.end_time))

        event = Event.objects.create(
            title=routine.name,
            description=routine.instruction,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            is_recurring=True,
            routine=routine
        )
        
def create_event_for_daily_goal(daily_goal):
    from .models import Event, Routine, DailyGoal, DayGoal
    start_time = daily_goal.start_time
    end_time = daily_goal.end_time
    date = daily_goal.date  # Assuming date is already a DateField in DailyGoal

    start_datetime = timezone.make_aware(timezone.datetime.combine(date, start_time))
    end_datetime = timezone.make_aware(timezone.datetime.combine(date, end_time))

    event = Event.objects.create(
        title=daily_goal.goal,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        goal=daily_goal,
    )

    return event
