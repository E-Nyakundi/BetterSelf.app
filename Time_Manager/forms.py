from django import forms
from .models import Routine, Goals, YearlyGoal, MonthlyGoal, WeeklyGoal, DayGoal, DailyGoal, Event
from .date_fields import PartialYearField, PartialMonthField, PartialDayField, PartialDateField


DAY_CHOICES = [
    (0, 'Monday'),
    (1, 'Tuesday'),
    (2, 'Wednesday'),
    (3, 'Thursday'),
    (4, 'Friday'),
    (5, 'Saturday'),
    (6, 'Sunday'),
]

class RoutineForm(forms.ModelForm):
    days_of_week = forms.MultipleChoiceField(
        choices=DAY_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    class Meta:
        model = Routine
        fields = ['name', 'instruction', 'start_time', 'end_time', 'is_weekend', 'days_of_week']

    def clean_days_of_week(self):
        days = self.cleaned_data.get('days_of_week', [])
        return [int(day) for day in days]

    def clean(self):
        cleaned_data = super().clean()
        is_weekend = cleaned_data.get('is_weekend')
        days_of_week = cleaned_data.get('days_of_week', [])
        days_as_ints = [int(day) if isinstance(day, str) else day for day in days_of_week]

        if is_weekend and any(day < 5 for day in days_as_ints):
            raise forms.ValidationError("Weekend routines should not include weekdays (Monday-Friday).")
        if not is_weekend and any(day >= 5 for day in days_as_ints):
            raise forms.ValidationError("Weekday routines should not include weekend days (Saturday-Sunday).")

        return cleaned_data


class GoalForm(forms.ModelForm):
    start_year = PartialYearField(label='Start Year (e.g., 2026)', required=False)
    end_year = PartialYearField(label='End Year (e.g., 2026)', required=False)
    
    class Meta:
        model = Goals
        fields = ['name', 'description', 'start_year', 'end_year']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add CSS classes
        self.fields['name'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Enter goal name'})
        self.fields['description'].widget.attrs.update({'class': 'form-control', 'rows': 3, 'placeholder': 'Enter goal description'})
        self.fields['start_year'].widget.attrs.update({'class': 'form-control'})
        self.fields['end_year'].widget.attrs.update({'class': 'form-control'})

        
class YearlyGoalForm(forms.ModelForm):
    year = PartialYearField(label='Year (e.g., 2026)', required=False)
    
    class Meta:
        model = YearlyGoal
        fields = ['goal', 'description', 'completed', 'year', 'goals']

class MonthlyGoalForm(forms.ModelForm):
    month = PartialMonthField(label='Month (e.g., Feb or 02)', required=False)
    
    class Meta:
        model = MonthlyGoal
        fields = ['goal', 'description', 'completed', 'month', 'yearly_goal']

class WeeklyGoalForm(forms.ModelForm):
    start_date = PartialDateField(label='Week Start (Year, Month, Day)', required=False)
    end_date = PartialDateField(label='Week End (Year, Month, Day)', required=False)
    
    class Meta:
        model = WeeklyGoal
        fields = ['goal', 'description', 'completed', 'start_date', 'end_date', 'monthly_goal']

class DayGoalForm(forms.ModelForm):
    date = PartialDateField(label='Date (Year, Month, Day)', required=False)
    
    class Meta:
        model = DayGoal
        fields = ['goal', 'description', 'date', 'completed', 'weekly_goal']


class DailyGoalForm(forms.ModelForm):
    date = PartialDateField(label='Date (Year, Month, Day)', required=False)
    
    class Meta:
        model = DailyGoal
        fields = ['goal', 'description', 'completed', 'date', 'start_time', 'end_time', 'day_goal']


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        exclude = ['user']
        widgets = {
            'start_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
        }