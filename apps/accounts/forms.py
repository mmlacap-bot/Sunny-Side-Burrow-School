from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from apps.student.models import Student, Teacher

User = get_user_model()

# ============================================================================
# AUTHENTICATION FORMS
# ============================================================================

class LoginForm(forms.Form):
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('teacher', 'Teacher'),
        ('administrator', 'Administrator'),
    ]

    role = forms.ChoiceField(choices=ROLE_CHOICES, label='Role')
    email = forms.CharField(label='Login Email or Username', max_length=254)
    password = forms.CharField(widget=forms.PasswordInput, label='Password')


class StudentRegistrationForm(forms.Form):
    first_name = forms.CharField(max_length=100, label='First Name', required=True)
    last_name = forms.CharField(max_length=100, label='Last Name', required=True)
    middle_name = forms.CharField(max_length=100, required=False, label='Middle Name')
    email = forms.EmailField(label='Email Address (for notifications)', required=True)
    birthdate = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), label='Date of Birth', required=True)
    gender = forms.ChoiceField(choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')], label='Gender', required=True)
    contact_number = forms.CharField(max_length=15, label='Phone Number', required=True)
    address = forms.CharField(widget=forms.Textarea, required=False, label='Home Address')
    guardian_name = forms.CharField(max_length=100, required=False, label='Guardian Name')
    guardian_contact = forms.CharField(max_length=15, required=False, label='Guardian Contact Number')
    password = forms.CharField(widget=forms.PasswordInput, label='Password', required=True)

    def clean_email(self):
        email = self.cleaned_data.get('email', '')
        if User.objects.filter(email=email).exists():
            raise ValidationError('This email is already registered.')
        return email


class TeacherRegistrationForm(forms.Form):
    first_name = forms.CharField(max_length=100, label='First Name', required=True)
    last_name = forms.CharField(max_length=100, label='Last Name', required=True)
    middle_name = forms.CharField(max_length=100, required=False, label='Middle Name')
    email = forms.EmailField(label='Email Address', required=True)
    birthdate = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), label='Date of Birth', required=True)
    gender = forms.ChoiceField(choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')], label='Gender', required=True)
    contact_number = forms.CharField(max_length=20, label='Phone Number', required=True)
    address = forms.CharField(widget=forms.Textarea, required=False, label='Address')
    employee_id = forms.CharField(max_length=20, required=False, label='Employee ID')
    password = forms.CharField(widget=forms.PasswordInput, label='Password', required=True)

    def clean_email(self):
        email = self.cleaned_data.get('email', '')
        if User.objects.filter(email=email).exists():
            raise ValidationError('This email is already registered.')
        return email


class ProfilePhotoForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['photo']
        widgets = {
            'photo': forms.FileInput(attrs={'accept': 'image/*'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['photo'].required = False

    def clean_photo(self):
        photo = self.cleaned_data.get('photo')
        if photo and photo.size > 5 * 1024 * 1024:
            raise ValidationError('Image must be 5 MB or smaller.')
        return photo


class StudentPhotoForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['photo']
        widgets = {
            'photo': forms.FileInput(attrs={'accept': 'image/*'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['photo'].required = False

    def clean_photo(self):
        photo = self.cleaned_data.get('photo')
        if photo and photo.size > 5 * 1024 * 1024:
            raise ValidationError('Image must be 5 MB or smaller.')
        return photo


class StudentProfileForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['first_name', 'last_name', 'middle_name', 'birthdate', 'gender', 
                  'address', 'contact_number', 'guardian_name', 'guardian_contact', 'photo']
        widgets = {
            'birthdate': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 3}),
            'photo': forms.FileInput(attrs={'accept': 'image/*'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            if field != 'photo':
                self.fields[field].widget.attrs['class'] = 'form-control'


class TeacherProfileForm(forms.ModelForm):
    class Meta:
        model = Teacher
        fields = ['first_name', 'last_name', 'middle_name', 'birthdate', 'gender',
                  'address', 'contact_number', 'photo']
        widgets = {
            'birthdate': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 3}),
            'photo': forms.FileInput(attrs={'accept': 'image/*'}),
        }


class ChangePasswordForm(forms.Form):
    current_password = forms.CharField(widget=forms.PasswordInput, label='Current Password')
    new_password = forms.CharField(widget=forms.PasswordInput, label='New Password')
    new_password2 = forms.CharField(widget=forms.PasswordInput, label='Confirm New Password')

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_current_password(self):
        current_password = self.cleaned_data['current_password']
        if self.user and not self.user.check_password(current_password):
            raise ValidationError('Current password is incorrect.')
        return current_password

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('new_password') != cleaned.get('new_password2'):
            raise ValidationError('New passwords do not match.')
        return cleaned


# ============================================================================
# SECURITY & MFA FORMS
# ============================================================================

class UpdateEmailForm(forms.Form):
    email = forms.EmailField(label='New Registered Email', required=True)
    
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.exclude(pk=self.user.pk).filter(email=email).exists():
            raise ValidationError('This email is already taken.')
        return email


class MFASettingsForm(forms.Form):
    mfa_type = forms.ChoiceField(
        choices=User.MFA_CHOICES,
        label='MFA Method',
        widget=forms.RadioSelect
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for i in range(1, 9):
            self.fields[f'question_{i}'] = forms.CharField(
                max_length=255, 
                required=False, 
                label=f'Security Question {i}',
                widget=forms.TextInput(attrs={'placeholder': f'e.g., What was your first pet\'s name? ({i})'})
            )
            self.fields[f'answer_{i}'] = forms.CharField(
                max_length=255, 
                required=False, 
                label=f'Answer {i}',
                widget=forms.PasswordInput(render_value=True, attrs={'placeholder': 'Your secret answer'})
            )

    def clean(self):
        cleaned_data = super().clean()
        mfa_type = cleaned_data.get('mfa_type')
        
        if mfa_type == 'QUESTION':
            questions = []
            for i in range(1, 9):
                q = cleaned_data.get(f'question_{i}')
                a = cleaned_data.get(f'answer_{i}')
                
                if not q or not a:
                    self.add_error(f'question_{i}', f'Both question and answer are required for Question {i}.')
                
                if q:
                    if q.lower().strip() in questions:
                        self.add_error(f'question_{i}', 'Each security question must be unique.')
                    questions.append(q.lower().strip())
                
        return cleaned_data


class OTPVerifyForm(forms.Form):
    otp_code = forms.CharField(
        max_length=6,
        min_length=6,
        label='Verification Code',
        widget=forms.TextInput(attrs={'placeholder': '123456', 'autocomplete': 'one-time-code'})
    )


class SecurityQuestionVerifyForm(forms.Form):
    answer = forms.CharField(
        max_length=255,
        label='Your Answer',
        widget=forms.TextInput(attrs={'autocomplete': 'off'})
    )