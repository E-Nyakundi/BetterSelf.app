"""
Custom form fields and widgets for partial date input.
"""

from django import forms
from django.core.exceptions import ValidationError
from datetime import date
from .date_utils import parse_partial_date, parse_year, parse_month, parse_day


class PartialDateMultiWidget(forms.MultiWidget):
    """
    Custom MultiWidget for partial date input (year, month, day).
    """
    def __init__(self):
        widgets = [
            forms.NumberInput(attrs={'placeholder': 'YYYY', 'type': 'text', 'size': '6'}),
            forms.TextInput(attrs={'placeholder': 'Month', 'type': 'text', 'size': '5'}),
            forms.TextInput(attrs={'placeholder': 'Day', 'type': 'text', 'size': '4'}),
        ]
        super().__init__(widgets)
    
    def decompress(self, value):
        """Break down a date object into year, month (abbr), day components."""
        if value:
            return [str(value.year), value.strftime('%b'), str(value.day)]
        return ['', '', '']


class PartialYearField(forms.Field):
    """
    Form field that accepts a year-only input.
    Stores as date(year, today.month, today.day).
    """
    widget = forms.NumberInput(attrs={'placeholder': 'YYYY', 'type': 'text'})
    
    def to_python(self, value):
        if not value:
            return None
        
        try:
            year = parse_year(value)
            today = date.today()
            return date(year, today.month, today.day)
        except (ValueError, TypeError) as e:
            raise ValidationError(f"Enter a valid year. {str(e)}")


class PartialMonthField(forms.Field):
    """
    Form field that accepts month name or digit.
    Accepts: "Feb", "2", "february"
    Stores as date(today.year, month, today.day).
    """
    widget = forms.TextInput(attrs={'placeholder': 'Feb or 02', 'type': 'text'})
    
    def to_python(self, value):
        if not value:
            return None
        
        try:
            month = parse_month(value)
            today = date.today()
            return date(today.year, month, today.day)
        except (ValueError, TypeError) as e:
            raise ValidationError(f"Enter a valid month (e.g., 'Feb' or '02'). {str(e)}")


class PartialDayField(forms.Field):
    """
    Form field that accepts day with optional ordinal suffix.
    Accepts: "15", "15th", "1st", "22nd"
    Stores as date(today.year, today.month, day).
    """
    widget = forms.TextInput(attrs={'placeholder': '15 or 15th', 'type': 'text'})
    
    def to_python(self, value):
        if not value:
            return None
        
        try:
            day = parse_day(value)
            today = date.today()
            return date(today.year, today.month, day)
        except (ValueError, TypeError) as e:
            raise ValidationError(f"Enter a valid day (e.g., '15' or '15th'). {str(e)}")


class PartialDateField(forms.Field):
    """
    Form field that accepts partial date input (year, month, day separately).
    Users can provide just the most specific component needed.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.widget = PartialDateMultiWidget()
    
    def to_python(self, value):
        if not value or value == ['', '', '']:
            return None
        
        year, month, day = value
        
        try:
            return parse_partial_date(
                year=year if year else None,
                month=month if month else None,
                day=day if day else None
            )
        except (ValueError, TypeError) as e:
            raise ValidationError(f"Invalid date input: {str(e)}")
