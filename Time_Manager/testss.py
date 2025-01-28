from .models import Goals, YearlyGoal, MonthlyGoal, WeeklyGoal, DailyGoal
WeeklyGoal.objects.filter(id=3).exists()
