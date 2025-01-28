from django import forms
from .models import Routine, Goals, YearlyGoal, MonthlyGoal, WeeklyGoal, DayGoal, DailyGoal

class RoutineForm(forms.ModelForm):
    class Meta:
        model = Routine
        fields = ['name', 'instruction', 'start_time', 'end_time', 'is_weekend']

class GoalForm(forms.ModelForm):
    class Meta:
        model = Goals
        fields = ['name', 'description', 'start_year', 'end_year']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add a CSS class to the 'name' field
        self.fields['name'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Enter goal name'})
        # Add a CSS class to the 'description' field
        self.fields['description'].widget.attrs.update({'class': 'form-control', 'rows': 3, 'placeholder': 'Enter goal description'})
        # Add a CSS class to the 'start_year' field
        self.fields['start_year'].widget.attrs.update({'class': 'form-control', 'placeholder': 'YYYY'})
        # Add a CSS class to the 'end_year' field
        self.fields['end_year'].widget.attrs.update({'class': 'form-control', 'placeholder': 'YYYY'})

        
class YearlyGoalForm(forms.ModelForm):
    class Meta:
        model = YearlyGoal
        fields = ['goal', 'description', 'completed', 'year', 'goals']

class MonthlyGoalForm(forms.ModelForm):
    class Meta:
        model = MonthlyGoal
        fields = ['goal', 'description', 'completed', 'month', 'yearly_goal']

class WeeklyGoalForm(forms.ModelForm):
    class Meta:
        model = WeeklyGoal
        fields = ['goal', 'description', 'completed', 'start_date', 'end_date', 'monthly_goal']

class DayGoalForm(forms.ModelForm):

    class Meta:
        model = DayGoal
        fields = ['goal', 'description', 'date', 'completed', 'weekly_goal']


class DailyGoalForm(forms.ModelForm):
    class Meta:
        model = DailyGoal
        fields = ['goal', 'description', 'completed', 'date', 'start_time', 'end_time', 'day_goal']
