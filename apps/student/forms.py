from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import (
    Student, Teacher, Enrollment, Payment, Concern, EnrollmentSubject
)
from apps.academics.models import (
    ClassSchedule, Section, SchoolYear, GradeLevel, Subject
)

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
    login_email = forms.CharField(label='Login Email or Username', max_length=254)
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
# STUDENT FORMS
# ============================================================================

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


# ============================================================================
# TEACHER FORMS
# ============================================================================

class TeacherPhotoForm(forms.ModelForm):
    class Meta:
        model = Teacher
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


class TeacherAdviserSubjectsForm(forms.Form):
    adviser_section = forms.ModelChoiceField(queryset=Section.objects.none(), required=True, label='Adviser Section')
    subjects = forms.ModelMultipleChoiceField(
        queryset=Subject.objects.none(),
        required=True,
        label='Subjects (choose at least 2)',
        widget=forms.CheckboxSelectMultiple,
    )

    def __init__(self, *args, teacher=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.teacher = teacher

        active_year = SchoolYear.objects.filter(is_active=True).first()
        if active_year:
            self.fields['adviser_section'].queryset = Section.objects.filter(
                school_year=active_year,
            ).select_related('grade_level', 'school_year').order_by('grade_level__level_order', 'name')
        else:
            self.fields['adviser_section'].queryset = Section.objects.select_related('grade_level', 'school_year').order_by(
                'school_year__year_start', 'grade_level__level_order', 'name'
            )

        self.fields['subjects'].queryset = Subject.objects.select_related('grade_level').order_by('grade_level__level_order', 'code')

        if teacher is not None and not self.is_bound:
            # Adviser section = currently assigned section (if any)
            existing_section = Section.objects.filter(teacher=teacher).select_related('grade_level', 'school_year').first()
            if existing_section:
                self.fields['adviser_section'].initial = existing_section
            self.fields['subjects'].initial = teacher.subjects.all()

    def clean_subjects(self):
        subjects = self.cleaned_data.get('subjects')
        if not subjects or len(subjects) < 2:
            raise ValidationError('Please select at least 2 subjects.')
        return subjects


# ============================================================================
# ENROLLMENT FORMS
# ============================================================================

class EnrollmentForm(forms.ModelForm):
    class Meta:
        model = Enrollment
        fields = ['school_year', 'grade_level', 'section']

    def __init__(self, *args, **kwargs):
        self.student = kwargs.pop('student', None)
        super().__init__(*args, **kwargs)

        active_school_year = SchoolYear.objects.filter(is_active=True).first()
        school_year_queryset = SchoolYear.objects.filter(is_active=True).order_by('-year_start')
        if not school_year_queryset.exists():
            school_year_queryset = SchoolYear.objects.order_by('-year_start')

        grade_level_queryset = GradeLevel.objects.all().order_by('level_order')
        if not grade_level_queryset.exists():
            grade_level_queryset = GradeLevel.objects.order_by('level_order')

        section_queryset = Section.objects.select_related('grade_level', 'school_year').order_by(
            'school_year__year_start', 'grade_level__level_order', 'name'
        )

        self.fields['school_year'].queryset = school_year_queryset
        self.fields['grade_level'].queryset = grade_level_queryset
        self.fields['section'].queryset = section_queryset

        if not self.is_bound:
            if active_school_year:
                self.fields['school_year'].initial = active_school_year
            elif school_year_queryset.exists():
                self.fields['school_year'].initial = school_year_queryset.first()

            if grade_level_queryset.exists():
                self.fields['grade_level'].initial = grade_level_queryset.first()

            if self.fields['school_year'].initial and self.fields['grade_level'].initial:
                self.fields['section'].queryset = Section.objects.filter(
                    school_year=self.fields['school_year'].initial,
                    grade_level=self.fields['grade_level'].initial,
                ).select_related('grade_level', 'school_year').order_by(
                    'school_year__year_start', 'grade_level__level_order', 'name'
                )

        self.fields['school_year'].empty_label = 'Select school year'
        self.fields['grade_level'].empty_label = 'Select grade level'
        self.fields['section'].empty_label = 'Select section'

    def clean(self):
        cleaned = super().clean()
        school_year = cleaned.get('school_year')
        grade_level = cleaned.get('grade_level')
        section = cleaned.get('section')
        
        if section and grade_level and school_year:
            if section.grade_level_id != grade_level.id:
                raise ValidationError({'section': 'This section does not belong to the selected grade level.'})
            if section.school_year_id != school_year.id:
                raise ValidationError({'section': 'This section is not offered for the selected school year.'})
            
            # Check if section has capacity
            if not section.can_enroll():
                raise ValidationError({'section': 'This section is already full.'})
        
        if self.student and school_year:
            existing = Enrollment.objects.filter(student=self.student, school_year=school_year)
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise ValidationError('You already have an enrollment record for the selected school year.')
        
        return cleaned


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


class PaymentConfirmationForm(forms.ModelForm):
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


# ============================================================================
# SCHOOL DATA FORMS
# ============================================================================

class SchoolYearForm(forms.ModelForm):
    class Meta:
        model = SchoolYear
        fields = ['year_start', 'year_end', 'is_active']
        widgets = {
            'year_start': forms.NumberInput(attrs={'min': 2000, 'max': 3000}),
            'year_end': forms.NumberInput(attrs={'min': 2000, 'max': 3000}),
        }

    def clean(self):
        cleaned = super().clean()
        year_start = cleaned.get('year_start')
        year_end = cleaned.get('year_end')
        
        if year_start and year_end and year_start >= year_end:
            raise ValidationError('Start year must be before end year.')
        
        # Check for duplicate active school year
        if cleaned.get('is_active'):
            active = SchoolYear.objects.filter(is_active=True)
            if self.instance.pk:
                active = active.exclude(pk=self.instance.pk)
            if active.exists():
                raise ValidationError('Only one school year can be active at a time.')
        
        return cleaned


class GradeLevelForm(forms.ModelForm):
    class Meta:
        model = GradeLevel
        fields = ['name', 'level_order']
        widgets = {
            'level_order': forms.NumberInput(attrs={'min': 1}),
        }


class SectionForm(forms.ModelForm):
    class Meta:
        model = Section
        fields = ['name', 'grade_level', 'max_students', 'school_year', 'teacher']
        widgets = {
            'max_students': forms.NumberInput(attrs={'min': 1}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['teacher'].queryset = Teacher.objects.filter(status='Active')


class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['code', 'name', 'grade_level', 'units', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'units': forms.NumberInput(attrs={'step': '0.5', 'min': '0.5'}),
        }


class ClassScheduleForm(forms.ModelForm):
    class Meta:
        model = ClassSchedule
        fields = ['subject', 'section', 'day', 'time_start', 'time_end', 'room', 'teacher']
        widgets = {
            'time_start': forms.TimeInput(attrs={'type': 'time'}),
            'time_end': forms.TimeInput(attrs={'type': 'time'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['teacher'].queryset = Teacher.objects.filter(status='Active')

    def clean(self):
        cleaned = super().clean()
        time_start = cleaned.get('time_start')
        time_end = cleaned.get('time_end')
        
        if time_start and time_end and time_start >= time_end:
            raise ValidationError('Start time must be before end time.')
        
        return cleaned

    def clean_login_email(self):
        return self.cleaned_data['login_email'].strip().lower()
