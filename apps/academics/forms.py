from django import forms
from django.core.exceptions import ValidationError

from .models import SchoolYear, GradeLevel, Section, Subject, ClassSchedule
from apps.student.models import Teacher


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


class TeacherApplicationForm(forms.Form):
    APPLICATION_TYPES = [
        ('SUBJECT', 'Subject Assignment'),
        ('ADVISORY', 'Advisory Section'),
    ]
    application_type = forms.ChoiceField(choices=APPLICATION_TYPES, widget=forms.HiddenInput())
    class_schedules = forms.ModelMultipleChoiceField(
        queryset=ClassSchedule.objects.none(),
        widget=forms.CheckboxSelectMultiple(),
        required=False
    )
    section = forms.ModelChoiceField(
        queryset=Section.objects.none(),
        required=False,
        empty_label="Select Advisory Section"
    )
    notes = forms.CharField(widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Optional notes for your application...'}), required=False)

    def __init__(self, *args, **kwargs):
        school_year = kwargs.pop('school_year', None)
        super().__init__(*args, **kwargs)
        if school_year:
            # Exclude items that have pending or approved applications
            from .models import TeacherApplication
            occupied_schedule_ids = TeacherApplication.objects.filter(
                school_year=school_year,
                status__in=['PENDING', 'APPROVED'],
                class_schedule__isnull=False
            ).values_list('class_schedule_id', flat=True)
            
            occupied_section_ids = TeacherApplication.objects.filter(
                school_year=school_year,
                application_type='ADVISORY',
                status__in=['PENDING', 'APPROVED'],
                section__isnull=False
            ).values_list('section_id', flat=True)

            self.fields['class_schedules'].queryset = ClassSchedule.objects.filter(
                school_year=school_year,
                teacher__isnull=True
            ).exclude(id__in=occupied_schedule_ids).exclude(subject__name__iexact='Recess').order_by('section__grade_level__name', 'section__name', 'subject__name')
            
            self.fields['section'].queryset = Section.objects.filter(
                school_year=school_year,
                teacher__isnull=True
            ).exclude(id__in=occupied_section_ids).order_by('grade_level__name', 'name')


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


class ScheduleForm(forms.ModelForm):
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