from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from .models import Routine, Goals, YearlyGoal, MonthlyGoal, WeeklyGoal, DayGoal, DailyGoal, Event
from .forms import RoutineForm, GoalForm, YearlyGoalForm, MonthlyGoalForm, WeeklyGoalForm, DayGoalForm, DailyGoalForm, EventForm
from .utils import build_schedule_for_date
from django.http import JsonResponse
from datetime import date
import logging
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction


logger = logging.getLogger(__name__)


class RoutineView(LoginRequiredMixin, View):
    template_name = 'Time_Manager/routines.html'

    def get(self, request, routine_id=None):
        if routine_id:
            routine = get_object_or_404(Routine, id=routine_id, user=request.user)
            if routine.is_split:
                return redirect('routine')  # Prevent editing split routines
            form = RoutineForm(instance=routine)
        else:
            routine = None
            form = RoutineForm()

        routines = Routine.objects.filter(user=request.user, is_weekend=False, is_split=False)
        weekend_routines = Routine.objects.filter(user=request.user, is_weekend=True, is_split=False)

        context = {
            'form': form,
            'routine': routine,
            'routines': routines,
            'weekend_routines': weekend_routines
        }
        return render(request, self.template_name, context)

    def post(self, request, routine_id=None):
        if routine_id:
            routine = get_object_or_404(Routine, id=routine_id, user=request.user)
            form = RoutineForm(request.POST, instance=routine)
        else:
            form = RoutineForm(request.POST)

        if form.is_valid():
            routine = form.save(commit=False)
            routine.user = request.user

            try:
                with transaction.atomic():
                    if routine_id:
                        Routine.objects.filter(original_routine=routine, is_split=True).delete()
                    routine.save()
                    return redirect('routine')

            except Exception as e:
                form.add_error(None, f"Error saving routine: {str(e)}")

        routines = Routine.objects.filter(user=request.user, is_weekend=False, is_split=False)
        weekend_routines = Routine.objects.filter(user=request.user, is_weekend=True, is_split=False)

        context = {
            'form': form,
            'routine': routine if routine_id else None,
            'routines': routines,
            'weekend_routines': weekend_routines
        }
        return render(request, self.template_name, context)

class DeleteRoutineView(LoginRequiredMixin, View):
    def post(self, request, routine_id):
        routine = get_object_or_404(Routine, id=routine_id, user=request.user)
        routine.delete()
        return redirect('routine')
    
@login_required
def ScheduleView(request):
    template_name = 'Time_Manager/schedule.html'

    # Get today's date (or selected date from the request)
    selected_date = request.GET.get('date', date.today().isoformat())
    try:
        today = date.fromisoformat(selected_date)
    except ValueError:
        today = date.today()

    # Shared helper — also used by Accounts.dashboard_helpers for the
    # "Next Up" card, so the two views can't drift out of sync.
    schedule = build_schedule_for_date(request.user, today)

    # Get the day's name (e.g., Monday, Tuesday)
    day_name = today.strftime('%A')  # Full day name
    
    # Pass the schedule to the template
    context = {
        'day': day_name,  # Add the day's name
        'date': today.strftime('%b. %d, %Y'),  # Format date as "Jan. 29, 2025"
        'schedule': schedule
    }
    return render(request, template_name, context)
# Goals View

class GoalsView(LoginRequiredMixin, View):
    template_name = 'Time_Manager/Goals.html'
    form_class = GoalForm
    model = Goals

    def get(self, request, goal_id=None):
        # If editing a goal, ensure it belongs to the current user.
        if goal_id:
            goal = get_object_or_404(Goals, id=goal_id, user=request.user)
            form = self.form_class(instance=goal)
        else:
            form = self.form_class()

        # Retrieve only the logged in user's goals.
        goals = Goals.objects.filter(user=request.user)
        context = {'form': form, 'goals': goals}
        return render(request, self.template_name, context)

    def post(self, request, goal_id=None):
        # If editing, retrieve the goal ensuring it belongs to the user.
        if goal_id:
            goal = get_object_or_404(Goals, id=goal_id, user=request.user)
            form = self.form_class(request.POST, instance=goal)
        else:
            form = self.form_class(request.POST)

        if form.is_valid():
            # For new goals, attach the current user before saving.
            goal_obj = form.save(commit=False)
            if not goal_id:
                goal_obj.user = request.user
            goal_obj.save()
            return redirect('goals')  # Ensure your URL name 'goals' is correctly set up.

        # Retrieve the current user's goals for the context.
        goals = Goals.objects.filter(user=request.user)
        context = {'form': form, 'goals': goals}
        return render(request, self.template_name, context)


# Create and Edit Goals View
class CreateGoalsView(LoginRequiredMixin, View):
    template_name = 'Time_Manager/create&edit_goals.html'
    form_class = GoalForm

    def get(self, request, goal_id=None):
        if goal_id:
            goal = get_object_or_404(Goals, id=goal_id, user=request.user)
            form = self.form_class(instance=goal)
        else:
            form = self.form_class()
        goals = Goals.objects.filter(user=request.user)  # Retrieve only the logged in user's goals
        
        context = {'form': form, 'goals': goals}
        return render(request, self.template_name, context)

    def post(self, request, goal_id=None):
        if goal_id:
            goal = get_object_or_404(Goals, id=goal_id, user=request.user)
            form = self.form_class(request.POST, instance=goal)
        else:
            form = self.form_class(request.POST)

        if form.is_valid():
            # For new goals, attach the current user before saving.
            goal_obj = form.save(commit=False)
            if not goal_id:
                goal_obj.user = request.user
            goal_obj.save()
            return redirect('goals')  # Ensure your URL name 'goals' is correctly set up.

        goals = Goals.objects.filter(user=request.user)  # Retrieve only the logged in user's goals
        context = {'form': form, 'goals': goals}
        return render(request, self.template_name, context)
    

        
# Yearly Goal View
class YearlyGoalView(LoginRequiredMixin, View):
    template_name = 'Time_Manager/YearlyGoals.html'
    form_class = YearlyGoalForm
    model = YearlyGoal

    def get(self, request, goal_id=None):
        if goal_id:
            goal = get_object_or_404(
                self.model.objects.filter(
                    id=goal_id,
                    goals__user=request.user
                )
            )
            form = self.form_class(instance=goal, user=request.user)
        else:
            form = self.form_class(user=request.user)
            goal = None

        context = {
            'form': form,
            'goal': goal,  # Pass the goal object to the template
        }
        return render(request, self.template_name, context)

    def post(self, request, goal_id=None):
        goal = None
        if goal_id:
            goal = get_object_or_404(
                self.model.objects.filter(
                    id=goal_id,
                    goals__user=request.user
                )
            )
            form = self.form_class(request.POST, instance=goal, user=request.user)
        else:
            form = self.form_class(request.POST, user=request.user)
        
        if form.is_valid():
            # For new goals, attach the current user before saving.
            goal_obj = form.save(commit=False)
            if not goal_id:
                goal_obj.user = request.user
            goal_obj.save()
            return redirect('goals')  # Ensure your URL name 'goals' is correctly set up.
        
        context = {
            'form': form,
            'goal': goal,  # Pass the goal object to the template
        }
        return render(request, self.template_name, context)

# Monthly Goal View
class MonthlyGoalView(LoginRequiredMixin, View):
    template_name = 'Time_Manager/MonthlyGoals.html'
    form_class = MonthlyGoalForm
    model = MonthlyGoal

    def get(self, request, goal_id=None):
        year_id = request.GET.get('year')
        if goal_id:
            goal = get_object_or_404(
                self.model.objects.filter(
                    id=goal_id,
                    yearly_goal__goals__user=request.user
                )
            )
            form = self.form_class(instance=goal, user=request.user)
        else:
            form = self.form_class(initial={'yearly_goal': year_id}, user=request.user)
            goal = None  # Set goal to None when creating a new goal
        
        context = {
            'form': form,
            'goal': goal,  # Pass the goal object to the template
        }
        return render(request, self.template_name, context)
    def post(self, request, goal_id=None):
        goal = None
        if goal_id:
            goal = get_object_or_404(
                self.model.objects.filter(
                    id=goal_id,
                    yearly_goal__goals__user=request.user
                )
            )
            form = self.form_class(request.POST, instance=goal, user=request.user)
        else:
            form = self.form_class(request.POST, user=request.user)
        
        if form.is_valid():
            # For new goals, attach the current user before saving.
            goal_obj = form.save(commit=False)
            if not goal_id:
                goal_obj.user = request.user
            goal_obj.save()
            return redirect('goals')  # Ensure your URL name 'goals' is correctly set up.
        
        context = {
            'form': form,
            'goal': goal,  # Pass the goal object to the template
        }
        return render(request, self.template_name, context)

# Weekly Goal View
class WeeklyGoalView(LoginRequiredMixin, View):
    template_name = 'Time_Manager/WeeklyGoals.html'
    form_class = WeeklyGoalForm
    model = WeeklyGoal

    def get(self, request, goal_id=None):
        month_id = request.GET.get('month')
        if goal_id:
            goal = get_object_or_404(
                self.model.objects.filter(
                    id=goal_id,
                    monthly_goal__yearly_goal__goals__user=request.user
                )
            )
            form = self.form_class(instance=goal, user=request.user)
        else:
            form = self.form_class(initial={'monthly_goal': month_id}, user=request.user)
            goal = None  # Set goal to None when creating a new goal
        
        context = {
            'form': form,
            'goal': goal,  # Pass the goal object to the template
        }
        return render(request, self.template_name, context)

    def post(self, request, goal_id=None):
        goal = None
        if goal_id:
            goal = get_object_or_404(
                self.model.objects.filter(
                    id=goal_id,
                    monthly_goal__yearly_goal__goals__user=request.user
                )
            )
            form = self.form_class(request.POST, instance=goal, user=request.user)
        else:
            form = self.form_class(request.POST, user=request.user)
        
        if form.is_valid():
            # For new goals, attach the current user before saving.
            goal_obj = form.save(commit=False)
            if not goal_id:
                goal_obj.user = request.user
            goal_obj.save()
            return redirect('goals')  # Ensure your URL name 'goals' is correctly set up.
        
        context = {
            'form': form,
            'goal': goal,  # Pass the goal object to the template
        }
        return render(request, self.template_name, context)

class DayGoalView(LoginRequiredMixin, View):
    template_name = 'Time_Manager/day_detail.html'
    form_class = DayGoalForm
    model = DayGoal

    def get(self, request, goal_id=None):
        week_id = request.GET.get('week')
        if goal_id:
            goal = get_object_or_404(
                self.model.objects.filter(
                    id=goal_id,
                    weekly_goal__monthly_goal__yearly_goal__goals__user=request.user
                )
            )

            form = self.form_class(instance=goal, user=request.user)
        else:
            form = self.form_class(initial={'weekly_goal': week_id}, user=request.user)
            goal = None
        
        context = {
            'form': form,
            'goal': goal,
        }
        return render(request, self.template_name, context)

    def post(self, request, goal_id=None):
        logger.info("DailyGoalView POST request received")  # Log the POST request
        goal = None
        if goal_id:
            goal = get_object_or_404(
                self.model.objects.filter(
                    id=goal_id,
                    weekly_goal__monthly_goal__yearly_goal__goals__user=request.user
                )
            )

            form = self.form_class(request.POST, instance=goal, user=request.user)
        else:
            form = self.form_class(request.POST, user=request.user)
        
        if form.is_valid():
            # For new goals, attach the current user before saving.
            goal_obj = form.save(commit=False)
            if not goal_id:
                goal_obj.user = request.user
            goal_obj.save()
            return redirect('goals')  # Ensure your URL name 'goals' is correctly set up.
        
        context = {
            'form': form,
            'goal': goal,
        }
        return render(request, self.template_name, context)
    
# Daily Goal View
class DailyGoalView(LoginRequiredMixin, View):
    template_name = 'Time_Manager/DailyGoals.html'
    form_class = DailyGoalForm
    model = DailyGoal

    def get(self, request, goal_id=None):
        day_id = request.GET.get('day')
        if goal_id:
            # Retrieve a specific goal by ID
            goal = get_object_or_404(
                self.model.objects.filter(
                    id=goal_id,
                    day_goal__weekly_goal__monthly_goal__yearly_goal__goals__user=request.user
                )
            )
            form = self.form_class(instance=goal, user=request.user)
        else:
            # Retrieve all goals related to the specific DayGoal, ordered by start_time
            goal = None
            form = self.form_class(initial={'day_goal': day_id}, user=request.user)

        context = {
            'form': form,
            'goal': goal
        }
        return render(request, self.template_name, context)

    def post(self, request, goal_id=None):
        logger.info("DailyGoalView POST request received")  # Log the POST request
        if goal_id:
            goal = get_object_or_404(
                self.model.objects.filter(
                    id=goal_id,
                    day_goal__weekly_goal__monthly_goal__yearly_goal__goals__user=request.user
                )
            )
            form = self.form_class(request.POST, instance=goal, user=request.user)
        else:
            form = self.form_class(request.POST, user=request.user)
        
        if form.is_valid():
            # For new goals, attach the current user before saving.
            goal_obj = form.save(commit=False)
            if not goal_id:
                goal_obj.user = request.user
            goal_obj.save()
            return redirect('goals')  # Ensure your URL name 'goals' is correctly set up.

        context = {
            'form': form,
            'goal': goal if goal_id else None,
        }
        return render(request, self.template_name, context)


# Delete Goal View

class DeleteGoalView(LoginRequiredMixin, View):
    def post(self, request, goal_type, goal_id):
        logger.info(f"DeleteGoalView POST request received. Goal Type: {goal_type}, Goal ID: {goal_id}")  # Log the request

        goal_type = goal_type.lower()  # Ensure goal_type is lowercase
        if  goal_type == 'main_goal':
            goal = get_object_or_404(Goals, id=goal_id, user=request.user)
        elif  goal_type == 'yearly':
            goal = get_object_or_404(YearlyGoal, id=goal_id, goals__user=request.user)
        elif goal_type == 'monthly':
            goal = get_object_or_404(MonthlyGoal, id=goal_id, yearly_goal__goals__user=request.user)
        elif goal_type == 'weekly':
            goal = get_object_or_404(WeeklyGoal, id=goal_id, monthly_goal__yearly_goal__goals__user=request.user)
        elif goal_type == 'days':
            goal = get_object_or_404(DayGoal, id=goal_id, weekly_goal__monthly_goal__yearly_goal__goals__user=request.user)
        elif goal_type == 'daily':
            goal = get_object_or_404(DailyGoal, id=goal_id, day_goal__weekly_goal__monthly_goal__yearly_goal__goals__user=request.user)
        else:
            logger.error(f"Invalid goal_type: {goal_type}")  # Log invalid goal_type
            return redirect('goals')
        
        logger.info(f"Deleting goal: {goal}")  # Log the goal being deleted
        goal.delete()  # Delete the goal
        logger.info(f"Goal deleted successfully: {goal}")  # Log successful deletion
        return redirect('goals')
    

class EventsView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        form = EventForm()
        return render(request, 'Time_Manager/add_event.html', {'form': form})

    def post(self, request, *args, **kwargs):
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.user = request.user
            event.save()
            return redirect('scheduller')
        return render(request, 'Time_Manager/add_event.html', {'form': form})

@login_required
def get_events(request):
    daily_goals = DailyGoal.objects.filter(
        day_goal__weekly_goal__monthly_goal__yearly_goal__goals__user=request.user
    )
    routines = Routine.objects.filter(user=request.user)

    goals = [
        {
            'day': goal.date.day,
            'month': goal.date.month,
            'year': goal.date.year,
            'events': [{
                'title': goal.goal,
                'time': f"{goal.start_time.strftime('%I:%M %p')} - {goal.end_time.strftime('%I:%M %p')}"
            }]
        }
        for goal in daily_goals
        if goal.date and goal.start_time and goal.end_time
    ]

    today = date.today()
    routine_events = [
        {
            'day': today.day,
            'month': today.month,
            'year': today.year,
            'events': [{
                'title': routine.name,
                'time': f"{routine.start_time.strftime('%I:%M %p')} - {routine.end_time.strftime('%I:%M %p')}"
            }]
        }
        for routine in routines
    ]

    return JsonResponse(goals + routine_events, safe=False)
