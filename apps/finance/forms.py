from django import forms
from django.core.exceptions import ValidationError
import re

from apps.student.models import Payment


# ============================================================================
# PAYMENT FORMS
# ============================================================================

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['amount', 'payment_mode', 'reference_number', 'remarks']
        widgets = {
            'amount': forms.NumberInput(attrs={'step': '0.01', 'placeholder': '0.00'}),
            'remarks': forms.Textarea(attrs={'rows': 3}),
        }

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        if amount <= 0:
            raise ValidationError('Amount must be greater than zero.')
        return amount


class PaymentConfirmForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['status']

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('status') == 'CONFIRMED' and self.instance.status == 'CONFIRMED':
            raise ValidationError('This payment is already confirmed.')
        return cleaned


class VoidPaymentForm(forms.Form):
    void_reason = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        label='Reason for Voiding'
    )


class StudentPaymentSubmissionForm(forms.Form):
    PAYMENT_METHOD_CHOICES = [
        ('GCash', 'GCash'),
        ('Bank', 'Bank'),
    ]

    payment_mode = forms.ChoiceField(
        choices=PAYMENT_METHOD_CHOICES,
        widget=forms.RadioSelect,
        label='Payment Method',
    )
    amount = forms.DecimalField(max_digits=10, decimal_places=2, label='Amount Paid')
    reference_number = forms.CharField(max_length=50, label='Reference / Transaction ID')
    proof_of_payment = forms.ImageField(label='Proof of Payment')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['amount'].widget.attrs.update(
            {'class': 'form-control', 'placeholder': '0.00', 'step': '0.01'}
        )
        self.fields['reference_number'].widget.attrs.update(
            {'class': 'form-control', 'placeholder': 'Enter reference here'}
        )
        self.fields['proof_of_payment'].widget.attrs.update({'class': 'form-control'})

    def clean_reference_number(self):
        reference = self.cleaned_data['reference_number'].strip()
        if not re.fullmatch(r'[A-Za-z0-9\-]{8,50}', reference):
            raise ValidationError(
                'Reference ID must be 8-50 characters and can only include letters, numbers, and hyphens.'
            )
        return reference

    def clean_proof_of_payment(self):
        file = self.cleaned_data['proof_of_payment']
        if file.size > 5 * 1024 * 1024:
            raise ValidationError('Proof of payment must be 5MB or smaller.')
        return file