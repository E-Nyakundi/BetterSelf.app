from datetime import datetime, timedelta
from django.utils.dateparse import parse_datetime
from django.utils import timezone

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
