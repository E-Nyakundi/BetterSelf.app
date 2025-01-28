from django.contrib import admin
from .models import Schedule, Routine, Goals, YearlyGoal, MonthlyGoal, WeeklyGoal, DailyGoal, Event



#configurations
class ScheduleAdmin(admin.ModelAdmin):
    pass
class RoutineAdmin(admin.ModelAdmin):
    list_display = ['name', 'start_time', 'end_time']
    
class GoalsAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'start_datetime', 'end_datetime', 'is_recurring')
    
    
# Register your models here.
admin.site.register(Schedule, ScheduleAdmin)
admin.site.register(Routine, RoutineAdmin)
admin.site.register(Goals, GoalsAdmin)
admin.site.register(YearlyGoal)
admin.site.register(MonthlyGoal)
admin.site.register(WeeklyGoal)
admin.site.register(DailyGoal)
admin.site.register(Event, EventAdmin)    