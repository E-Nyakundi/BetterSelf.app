from django.shortcuts import render, get_object_or_404, redirect, HttpResponseRedirect
from django.views import View
from .models import Schedule, Routine, Goals, YearlyGoal, MonthlyGoal, WeeklyGoal, DailyGoal, Event
from .forms import RoutineForm, GoalForm, YearlyGoalForm, MonthlyGoalForm, WeeklyGoalForm, DailyGoalForm
from django.core.serializers.json import DjangoJSONEncoder
import json
from django.http import JsonResponse
from datetime import date, timedelta
import logging
from django.urls import reverse


logger = logging.getLogger(__name__)


# Dashboard View
def DashboardView(request):
    template_name = 'Time_Manager/tm_dashboard.html'
    return render(request, template_name)

# Schedule View
def ScheduleView(request):
    template_name = 'Time_Manager/schedule.html'
    events = Event.objects.all()
    events_list = []

    for event in events:
        if event.goal:
            goal_data = {
                'id': event.goal.id,
                'goal': event.goal.goal,
                'description': event.goal.description,
                'completed': event.goal.completed,
                'date': event.goal.date.strftime('%Y-%m-%d') if event.goal.date else None,
                'start_time': event.goal.start_time.strftime('%H:%M:%S') if event.goal.start_time else None,
                'end_time': event.goal.end_time.strftime('%H:%M:%S') if event.goal.end_time else None,
            }
        else:
            goal_data = None
        
        events_list.append({
            'title': event.title,
            'description': event.description,
            'start_datetime': event.start_datetime.strftime('%Y-%m-%d %H:%M:%S'),
            'end_datetime': event.end_datetime.strftime('%Y-%m-%d %H:%M:%S'),
            'is_recurring': event.is_recurring,
            'routine': event.routine.name if event.routine else None,
            'goal': goal_data,
        })

    events_json = json.dumps(events_list, cls=DjangoJSONEncoder)
    return render(request, template_name, {'events_json': events_json})

# Routine View
class RoutineView(View):
    template_name = 'Time_Manager/routines.html'
    model = Routine

    def get(self, request, routine_id=None):
        if routine_id:
            routine = get_object_or_404(Routine, id=routine_id)
            form = RoutineForm(instance=routine)
        else:
            form = RoutineForm()
        
        routines = Routine.objects.filter(is_weekend=False)
        weekend_routines = Routine.objects.filter(is_weekend=True)
        
        context = {
            'form': form,
            'routines': routines,
            'weekend_routines': weekend_routines
        }
        return render(request, self.template_name, context)
    
    def post(self, request, routine_id=None):
        if routine_id:
            routine = get_object_or_404(Routine, id=routine_id)
            form = RoutineForm(request.POST, instance=routine)
        else:
            form = RoutineForm(request.POST)
        
        if form.is_valid():
            form.save()
            return redirect('routine')
        
        routines = Routine.objects.filter(is_weekend=False)
        weekend_routines = Routine.objects.filter(is_weekend=True)
        
        context = {
            'form': form,
            'routines': routines,
            'weekend_routines': weekend_routines
        }
        return render(request, self.template_name, context)

# Goals View
class GoalsView(View):
    template_name = 'Time_Manager/Goals.html'
    form_class = GoalForm

    def get(self, request, goal_id=None):
        if goal_id:
            goal = get_object_or_404(Goals, id=goal_id)
            form = self.form_class(instance=goal)
        else:
            form = self.form_class()
        goals = Goals.objects.all()
        context = {'form': form, 'goals': goals}
        return render(request, self.template_name, context)

    def post(self, request, goal_id=None):
        if goal_id:
            goal = get_object_or_404(Goals, id=goal_id)
            form = self.form_class(request.POST, instance=goal)
        else:
            form = self.form_class(request.POST)

        if form.is_valid():
            form.save()
            return redirect('goals')

        goals = Goals.objects.all()
        context = {'form': form, 'goals': goals}
        return render(request, self.template_name, context)

# Create and Edit Goals View
class CreateGoalsView(View):
    template_name = 'Time_Manager/create&edit_goals.html'
    form_class = GoalForm

    def get(self, request, goal_id=None):
        if goal_id:
            goal = get_object_or_404(Goals, id=goal_id)
            form = self.form_class(instance=goal)
        else:
            form = self.form_class()
        goals = Goals.objects.all()
        context = {'form': form, 'goals': goals}
        return render(request, self.template_name, context)

    def post(self, request, goal_id=None):
        if goal_id:
            goal = get_object_or_404(Goals, id=goal_id)
            form = self.form_class(request.POST, instance=goal)
        else:
            form = self.form_class(request.POST)

        if form.is_valid():
            form.save()
            return redirect('goals')

        goals = Goals.objects.all()
        context = {'form': form, 'goals': goals}
        return render(request, self.template_name, context)
    

        
# Yearly Goal View
class YearlyGoalView(View):
    template_name = 'Time_Manager/YearlyGoals.html'
    form_class = YearlyGoalForm
    model = YearlyGoal

    def get(self, request, goal_id=None):
        if goal_id:
            goal = get_object_or_404(self.model, id=goal_id)
            form = self.form_class(instance=goal)
        else:
            form = self.form_class()
            goal = None

        context = {
            'form': form,
            'goal': goal,  # Pass the goal object to the template
        }
        return render(request, self.template_name, context)

    def post(self, request, goal_id=None):
        if goal_id:
            goal = get_object_or_404(self.model, id=goal_id)
            form = self.form_class(request.POST, instance=goal)
        else:
            form = self.form_class(request.POST)
        
        if form.is_valid():
            form.save()
            return redirect('goals')
        
        context = {
            'form': form,
            'goal': goal,  # Pass the goal object to the template
        }
        return render(request, self.template_name, context)

# Monthly Goal View
class MonthlyGoalView(View):
    template_name = 'Time_Manager/MonthlyGoals.html'
    form_class = MonthlyGoalForm
    model = MonthlyGoal

    def get(self, request, goal_id=None):
        year_id = request.GET.get('year')
        if goal_id:
            goal = get_object_or_404(self.model, id=goal_id)
            form = self.form_class(instance=goal)
        else:
            form = self.form_class(initial={'yearly_goal': year_id})
            goal = None  # Set goal to None when creating a new goal
        
        context = {
            'form': form,
            'goal': goal,  # Pass the goal object to the template
        }
        return render(request, self.template_name, context)
    def post(self, request, goal_id=None):
        if goal_id:
            goal = get_object_or_404(self.model, id=goal_id)
            form = self.form_class(request.POST, instance=goal)
        else:
            form = self.form_class(request.POST)
        
        if form.is_valid():
            form.save()
            return redirect('goals')
        
        context = {
            'form': form,
            'goal': goal,  # Pass the goal object to the template
        }
        return render(request, self.template_name, context)

# Weekly Goal View
class WeeklyGoalView(View):
    template_name = 'Time_Manager/WeeklyGoals.html'
    form_class = WeeklyGoalForm
    model = WeeklyGoal

    def get(self, request, goal_id=None):
        month_id = request.GET.get('month')
        if goal_id:
            goal = get_object_or_404(self.model, id=goal_id)
            form = self.form_class(instance=goal)
        else:
            form = self.form_class(initial={'monthly_goal': month_id})
            goal = None  # Set goal to None when creating a new goal
        
        context = {
            'form': form,
            'goal': goal,  # Pass the goal object to the template
        }
        return render(request, self.template_name, context)

    def post(self, request, goal_id=None):
        if goal_id:
            goal = get_object_or_404(self.model, id=goal_id)
            form = self.form_class(request.POST, instance=goal)
        else:
            form = self.form_class(request.POST)
        
        if form.is_valid():
            form.save()
            return redirect('goals')
        
        context = {
            'form': form,
            'goal': goal,  # Pass the goal object to the template
        }
        return render(request, self.template_name, context)

# Daily Goal View
class DailyGoalView(View):
    template_name = 'Time_Manager/DailyGoals.html'
    form_class = DailyGoalForm
    model = DailyGoal

    def get(self, request, goal_id=None):
        week_id = request.GET.get('week')
        if goal_id:
            goal = get_object_or_404(self.model, id=goal_id)
            form = self.form_class(instance=goal)
        else:
            form = self.form_class(initial={'weekly_goal': week_id})
            goal = None
        
        context = {
            'form': form,
            'goal': goal,
        }
        return render(request, self.template_name, context)

    def post(self, request, goal_id=None):
        logger.info("DailyGoalView POST request received")  # Log the POST request
        if goal_id:
            goal = get_object_or_404(self.model, id=goal_id)
            form = self.form_class(request.POST, instance=goal)
        else:
            form = self.form_class(request.POST)
        
        if form.is_valid():
            form.save()
            return redirect('goals')
        
        context = {
            'form': form,
            'goal': goal,
        }
        return render(request, self.template_name, context)

# Delete Goal View
class DeleteGoalView(View):
    def post(self, request, goal_type, goal_id):
        logger.info(f"DeleteGoalView POST request received. Goal Type: {goal_type}, Goal ID: {goal_id}")  # Log the request

        goal_type = goal_type.lower()  # Ensure goal_type is lowercase
        if goal_type == 'yearly':
            goal = get_object_or_404(YearlyGoal, id=goal_id)
        elif goal_type == 'monthly':
            goal = get_object_or_404(MonthlyGoal, id=goal_id)
        elif goal_type == 'weekly':
            goal = get_object_or_404(WeeklyGoal, id=goal_id)
        elif goal_type == 'daily':
            goal = get_object_or_404(DailyGoal, id=goal_id)
        else:
            logger.error(f"Invalid goal_type: {goal_type}")  # Log invalid goal_type
            return redirect('goals')
        
        logger.info(f"Deleting goal: {goal}")  # Log the goal being deleted
        goal.delete()  # Delete the goal
        logger.info(f"Goal deleted successfully: {goal}")  # Log successful deletion
        return redirect('goals')
    
def get_events(request):
    # Fetch all daily goals and routines
    daily_goals = DailyGoal.objects.all()
    routines = Routine.objects.all()

    # Process daily goals
    goals = [
        {
            'day': goal.date.day,
            'month': goal.date.month,
            'year': goal.date.year,
            'events': [{'title': goal.name, 'time': goal.time_period}]
        }
        for goal in daily_goals
    ]

    # Process routines
    today = date.today()
    routines = [
        {
            'day': today.day,
            'month': today.month,
            'year': today.year,
            'events': [{'title': routine.name, 'time': routine.time_period}]
        }
        for routine in routines
    ]

    # Combine goals and routines
    events = goals + routines

    return JsonResponse(events, safe=False)