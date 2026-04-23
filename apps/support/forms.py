from django import forms

from apps.student.models import Concern


# ============================================================================
# CONCERN FORMS
# ============================================================================

class ConcernForm(forms.ModelForm):
    class Meta:
        model = Concern
        fields = ['subject_text', 'description']
        widgets = {
            'subject_text': forms.TextInput(attrs={'placeholder': 'Subject of concern'}),
            'description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Describe your concern in detail'}),
        }


class ConcernResponseForm(forms.ModelForm):
    class Meta:
        model = Concern
        fields = ['status', 'response']
        widgets = {
            'response': forms.Textarea(attrs={'rows': 4}),
        }


class ResolveConcernForm(forms.Form):
    response = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4}),
        label='Response',
        required=False
    )