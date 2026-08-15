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

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # Accept user to scope the parent Goals queryset
        self.user = user
        super().__init__(*args, **kwargs)
        if user:
            self.fields['goals'].queryset = Goals.objects.filter(user=user)
        else:
            self.fields['goals'].queryset = Goals.objects.none()

    def clean_goals(self):
        goals = self.cleaned_data.get('goals')
        if goals and (not self.user or goals.user_id != self.user.id):
            raise forms.ValidationError("Choose one of your own goals.")
        return goals

class MonthlyGoalForm(forms.ModelForm):
    month = PartialMonthField(label='Month (e.g., Feb or 02)', required=False)
    
    class Meta:
        model = MonthlyGoal
        fields = ['goal', 'description', 'completed', 'month', 'yearly_goal']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # Accept user to scope the parent YearlyGoal queryset
        self.user = user
        super().__init__(*args, **kwargs)
        if user:
            self.fields['yearly_goal'].queryset = YearlyGoal.objects.filter(goals__user=user)
        else:
            self.fields['yearly_goal'].queryset = YearlyGoal.objects.none()

    def clean_yearly_goal(self):
        yearly_goal = self.cleaned_data.get('yearly_goal')
        if yearly_goal and (not self.user or not yearly_goal.goals or yearly_goal.goals.user_id != self.user.id):
            raise forms.ValidationError("Choose one of your own yearly goals.")
        return yearly_goal

class WeeklyGoalForm(forms.ModelForm):
    start_date = PartialDateField(label='Week Start (Year, Month, Day)', required=False)
    end_date = PartialDateField(label='Week End (Year, Month, Day)', required=False)
    
    class Meta:
        model = WeeklyGoal
        fields = ['goal', 'description', 'completed', 'start_date', 'end_date', 'monthly_goal']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # Accept user to scope the parent MonthlyGoal queryset
        self.user = user
        super().__init__(*args, **kwargs)
        if user:
            self.fields['monthly_goal'].queryset = MonthlyGoal.objects.filter(yearly_goal__goals__user=user)
        else:
            self.fields['monthly_goal'].queryset = MonthlyGoal.objects.none()

    def clean_monthly_goal(self):
        monthly_goal = self.cleaned_data.get('monthly_goal')
        if monthly_goal and (
            not self.user
            or not monthly_goal.yearly_goal
            or not monthly_goal.yearly_goal.goals
            or monthly_goal.yearly_goal.goals.user_id != self.user.id
        ):
            raise forms.ValidationError("Choose one of your own monthly goals.")
        return monthly_goal

class DayGoalForm(forms.ModelForm):
    date = PartialDateField(label='Date (Year, Month, Day)', required=False)
    
    class Meta:
        model = DayGoal
        fields = ['goal', 'description', 'date', 'completed', 'weekly_goal']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # Accept user to scope the parent WeeklyGoal queryset
        self.user = user
        super().__init__(*args, **kwargs)
        if user:
            self.fields['weekly_goal'].queryset = WeeklyGoal.objects.filter(monthly_goal__yearly_goal__goals__user=user)
        else:
            self.fields['weekly_goal'].queryset = WeeklyGoal.objects.none()

    def clean_weekly_goal(self):
        weekly_goal = self.cleaned_data.get('weekly_goal')
        if weekly_goal and (
            not self.user
            or not weekly_goal.monthly_goal
            or not weekly_goal.monthly_goal.yearly_goal
            or not weekly_goal.monthly_goal.yearly_goal.goals
            or weekly_goal.monthly_goal.yearly_goal.goals.user_id != self.user.id
        ):
            raise forms.ValidationError("Choose one of your own weekly goals.")
        return weekly_goal


class DailyGoalForm(forms.ModelForm):
    date = PartialDateField(label='Date (Year, Month, Day)', required=False)
    
    class Meta:
        model = DailyGoal
        fields = ['goal', 'description', 'completed', 'date', 'start_time', 'end_time', 'day_goal']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # Accept user to scope the parent DayGoal queryset
        self.user = user
        super().__init__(*args, **kwargs)
        if user:
            self.fields['day_goal'].queryset = DayGoal.objects.filter(
                weekly_goal__monthly_goal__yearly_goal__goals__user=user
            )
        else:
            self.fields['day_goal'].queryset = DayGoal.objects.none()

    def clean_day_goal(self):
        day_goal = self.cleaned_data.get('day_goal')
        if day_goal and (
            not self.user
            or not day_goal.weekly_goal
            or not day_goal.weekly_goal.monthly_goal
            or not day_goal.weekly_goal.monthly_goal.yearly_goal
            or not day_goal.weekly_goal.monthly_goal.yearly_goal.goals
            or day_goal.weekly_goal.monthly_goal.yearly_goal.goals.user_id != self.user.id
        ):
            raise forms.ValidationError("Choose one of your own day goals.")
        return day_goal


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