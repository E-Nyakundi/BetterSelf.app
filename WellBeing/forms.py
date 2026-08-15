from django import forms
from .models import JournalEntry


class JournalEntryForm(forms.ModelForm):
    class Meta:
        model = JournalEntry
        fields = [
            'entry', 'mood', 'energy', 'focus', 'sleep_hours',
            'went_well', 'needs_improvement',
            'image', 'video', 'audio', 'document',
        ]
        widgets = {
            'entry': forms.Textarea(attrs={'rows': 8, 'class': 'form-control'}),
            'went_well': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': "What went well today?"}),
            'needs_improvement': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': "What needs improvement?"}),
            'mood': forms.RadioSelect(attrs={'class': 'scale-input'}),
            'energy': forms.RadioSelect(attrs={'class': 'scale-input'}),
            'focus': forms.RadioSelect(attrs={'class': 'scale-input'}),
            'sleep_hours': forms.NumberInput(attrs={'step': '0.5', 'min': '0', 'max': '24', 'placeholder': 'e.g. 7.5'}),
            'image': forms.ClearableFileInput(attrs={'accept': 'image/*', 'capture': 'environment'}),
            'video': forms.ClearableFileInput(attrs={'accept': 'video/*', 'capture': 'user'}),
            'audio': forms.ClearableFileInput(attrs={'accept': 'audio/*', 'capture': 'user'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for scale_field in ('mood', 'energy', 'focus'):
            self.fields[scale_field].choices = [(i, str(i)) for i in range(1, 6)]
            self.fields[scale_field].required = False
            


