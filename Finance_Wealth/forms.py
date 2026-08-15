from django import forms
from .models import FinancialGoal


class FinancialGoalForm(forms.ModelForm):
    class Meta:
        model = FinancialGoal
        fields = ['name', 'category', 'target_amount', 'current_amount', 'target_date']
        widgets = {
            'target_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')

    def clean_target_amount(self):
        target_amount = self.cleaned_data.get('target_amount')
        if target_amount is not None and target_amount <= 0:
            raise forms.ValidationError("Target amount must be greater than zero.")
        return target_amount

    def clean_current_amount(self):
        current_amount = self.cleaned_data.get('current_amount')
        if current_amount is not None and current_amount < 0:
            raise forms.ValidationError("Current amount can't be negative.")
        return current_amount
