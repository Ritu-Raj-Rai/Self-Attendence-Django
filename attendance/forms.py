from django import forms
from .models import Subject

class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['name', 'target_percentage']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Mathematics'}),
            'target_percentage': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.1', 'min': '0', 'max': '100'}),
        }
