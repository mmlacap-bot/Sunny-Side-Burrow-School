from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings
from apps.core.models import BaseModel

# Import business logic constants
SECTION_DEFAULT_CAPACITY = getattr(settings, 'SECTION_DEFAULT_CAPACITY', 40)
SECTION_MIN_CAPACITY = getattr(settings, 'SECTION_MIN_CAPACITY', 10)


class SchoolYear(BaseModel):
    year_start = models.IntegerField()
    year_end = models.IntegerField()
    is_active = models.BooleanField(default=False)

    class Meta:
        ordering = ['-year_start']

    def clean(self):
        # Ensure only one active school year
        if self.is_active:
            active = SchoolYear.objects.filter(is_active=True).exclude(pk=self.pk)
            if active.exists():
                raise ValidationError('Only one school year can be active at a time')
        # Ensure year_start is before year_end
        if self.year_start >= self.year_end:
            raise ValidationError('Start year must be before end year')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.year_start}-{self.year_end}"


class GradeLevel(BaseModel):
    name = models.CharField(max_length=50)
    level_order = models.IntegerField()

    class Meta:
        ordering = ['level_order']

    def __str__(self):
        return self.name


class Section(BaseModel):
    name = models.CharField(max_length=50)
    grade_level = models.ForeignKey(GradeLevel, on_delete=models.CASCADE, related_name='sections')
    max_students = models.IntegerField(default=SECTION_DEFAULT_CAPACITY)
    school_year = models.ForeignKey(SchoolYear, on_delete=models.CASCADE, related_name='sections')
    teacher = models.ForeignKey('student.Teacher', on_delete=models.SET_NULL, null=True, blank=True, related_name='sections')

    class Meta:
        unique_together = ['name', 'grade_level', 'school_year']
        ordering = ['grade_level__level_order', 'name']

    @property
    def current_enrollment_count(self):
        return self.enrollments.filter(status__in=['Pending', 'Enrolled']).count()

    @property
    def available_slots(self):
        return self.max_students - self.current_enrollment_count

    def can_enroll(self):
        return self.current_enrollment_count < self.max_students

    def __str__(self):
        return f"{self.grade_level.name} - {self.name}"


class Subject(BaseModel):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20)
    grade_level = models.ForeignKey(GradeLevel, on_delete=models.CASCADE, related_name='subjects')
    units = models.DecimalField(max_digits=4, decimal_places=2, default=1.0)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['code']
        unique_together = [['code', 'grade_level']]

    def __str__(self):
        return f"{self.code} - {self.name}"


class ClassSchedule(BaseModel):
    DAYS = [
        ('Mon', 'Monday'),
        ('Tue', 'Tuesday'),
        ('Wed', 'Wednesday'),
        ('Thu', 'Thursday'),
        ('Fri', 'Friday'),
        ('Sat', 'Saturday'),
        ('MWF', 'MWF'),
        ('TTH', 'TTh'),
        ('Dly', 'Daily'),
    ]
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='schedules')
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='schedules')
    day = models.CharField(max_length=3, choices=DAYS)
    time_start = models.TimeField()
    time_end = models.TimeField()
    room = models.CharField(max_length=50)
    school_year = models.ForeignKey(SchoolYear, on_delete=models.CASCADE, related_name='schedules')
    teacher = models.ForeignKey('student.Teacher', on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_schedules')

    class Meta:
        ordering = ['day', 'time_start']
        unique_together = ['subject', 'section', 'school_year']

    @property
    def time_display(self):
        return f"{self.time_start.strftime('%H:%M')} - {self.time_end.strftime('%H:%M')}"

    def occurs_on(self, day_code):
        """Check if this schedule occurs on the given day code (e.g., 'Mon')"""
        if self.day == day_code:
            return True
        if self.day == 'MWF' and day_code in ['Mon', 'Wed', 'Fri']:
            return True
        if self.day == 'TTH' and day_code in ['Tue', 'Thu']:
            return True
        if self.day == 'Dly' and day_code in ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']:
            return True
        return False

    def __str__(self):
        return f"{self.subject.name} - {self.section.name} - {self.day}"

class TeacherApplication(BaseModel):
    APPLICATION_TYPES = [
        ('SUBJECT', 'Subject Assignment'),
        ('ADVISORY', 'Advisory Section'),
    ]
    STATUS_CHOICES = [
        ('PENDING', 'Pending Review'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]

    teacher = models.ForeignKey('student.Teacher', on_delete=models.CASCADE, related_name='applications')
    school_year = models.ForeignKey(SchoolYear, on_delete=models.CASCADE, related_name='teacher_applications')
    application_type = models.CharField(max_length=20, choices=APPLICATION_TYPES)
    class_schedule = models.ForeignKey(
        ClassSchedule,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='teacher_applications',
    )
    section = models.ForeignKey(
        Section,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='teacher_applications',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    notes = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_teacher_applications',
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def target_label(self):
        if self.application_type == 'SUBJECT' and self.class_schedule:
            return f"{self.class_schedule.subject.name} ({self.class_schedule.section.name})"
        if self.application_type == 'ADVISORY' and self.section:
            return f"Section {self.section.name} ({self.section.grade_level.name})"
        return "Unknown"

    def __str__(self):
        return f"{self.teacher.full_name} - {self.get_application_type_display()} - {self.status}"
