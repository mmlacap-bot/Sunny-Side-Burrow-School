from django import forms
from django.core.exceptions import ValidationError

from apps.student.models import Enrollment, EnrollmentSubject
from apps.academics.models import SchoolYear, GradeLevel, Section


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

        grade_level_queryset = GradeLevel.objects.filter(
            name__in=['Kinder', 'Preparatory', 'Grade 1', 'Grade 2', 'Grade 3', 'Grade 4', 'Grade 5', 'Grade 6']
        ).order_by('level_order')
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


class EnrollmentSubjectForm(forms.ModelForm):
    class Meta:
        model = EnrollmentSubject
        fields = ['class_schedule', 'status', 'grade']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['class_schedule'].disabled = True