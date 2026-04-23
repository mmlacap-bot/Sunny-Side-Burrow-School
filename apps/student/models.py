from django.db import models
from django.db.models import Max
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.utils import timezone

# Import business logic constants
DEFAULT_TUITION_FEE = getattr(settings, 'DEFAULT_TUITION_FEE', 10000)
STUDENT_ID_PREFIX = getattr(settings, 'STUDENT_ID_PREFIX', 'S')
PROFESSOR_ID_PREFIX = getattr(settings, 'PROFESSOR_ID_PREFIX', 'P')


class Student(models.Model):
    student_id = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True)
    birthdate = models.DateField()
    gender = models.CharField(max_length=10)
    address = models.TextField()
    contact_number = models.CharField(max_length=15)
    guardian_name = models.CharField(max_length=100)
    guardian_contact = models.CharField(max_length=15)
    photo = models.ImageField(upload_to='student_photos/', blank=True, null=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    class Meta:
        ordering = ['last_name', 'first_name']

    @classmethod
    def generate_student_id(cls):
        max_id = cls.objects.aggregate(max_id=Max('id'))['max_id'] or 0
        return f"{STUDENT_ID_PREFIX}{max_id + 1:04d}"

    def save(self, *args, **kwargs):
        if not self.student_id:
            self.student_id = self.generate_student_id()
        super().save(*args, **kwargs)

    @property
    def full_name(self):
        if self.middle_name:
            return f"{self.first_name} {self.middle_name} {self.last_name}"
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return self.full_name

class Enrollment(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Enrolled', 'Enrolled'),
        ('Fully Paid', 'Fully Paid'),
        ('Dropped', 'Dropped'),
        ('Transferred', 'Transferred'),
    ]
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='enrollments')
    school_year = models.ForeignKey('academics.SchoolYear', on_delete=models.CASCADE, related_name='enrollments')
    grade_level = models.ForeignKey('academics.GradeLevel', on_delete=models.CASCADE, related_name='enrollments')
    section = models.ForeignKey('academics.Section', on_delete=models.CASCADE, related_name='enrollments')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    tuition_fee = models.DecimalField(max_digits=10, decimal_places=2, default=DEFAULT_TUITION_FEE)
    enrolled_date = models.DateTimeField(default=timezone.now)
    enrolled_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='enrolled_students')
    notes = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        # Auto-update status to 'Fully Paid' if balance is zero and currently active
        if self.pk and self.status in ['Pending', 'Enrolled'] and self.balance == 0:
            self.status = 'Fully Paid'
        super().save(*args, **kwargs)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['student', 'school_year'],
                name='unique_student_school_year_enrollment',
            ),
        ]
        ordering = ['-enrolled_date']

    def __str__(self):
        return f"{self.student} - {self.school_year}"

    @property
    def total_paid(self):
        return sum(payment.amount for payment in self.payments.filter(status='CONFIRMED'))

    @property
    def balance(self):
        remaining = self.tuition_fee - self.total_paid
        return remaining if remaining > 0 else 0

    @property
    def payment_status(self):
        if self.balance == 0:
            return 'Paid'
        if self.total_paid > 0:
            return 'Partial'
        return 'Unpaid'

    @property
    def payment_percentage(self):
        if self.tuition_fee == 0:
            return 0
        return int((self.total_paid / self.tuition_fee) * 100)

class EnrollmentSubject(models.Model):
    STATUS_CHOICES = [
        ('Enrolled', 'Enrolled'),
        ('Dropped', 'Dropped'),
        ('Completed', 'Completed'),
    ]
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='subjects')
    class_schedule = models.ForeignKey('academics.ClassSchedule', on_delete=models.CASCADE, related_name='enrollments')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Enrolled')
    grade = models.CharField(max_length=5, blank=True)

    class Meta:
        unique_together = ['enrollment', 'class_schedule']
        ordering = ['enrollment', 'class_schedule__day', 'class_schedule__time_start']

    def __str__(self):
        return f"{self.enrollment.student} - {self.class_schedule.subject.name}"

class Payment(models.Model):
    PAYMENT_MODES = [
        ('Cash', 'Cash'),
        ('Check', 'Check'),
        ('Online', 'Online Transfer'),
        ('GCash', 'GCash'),
        ('Bank', 'Bank Deposit'),
    ]
    PAYMENT_STATUS = [
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('VOIDED', 'Voided'),
    ]
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField(default=timezone.now)
    payment_time = models.TimeField(default=timezone.now)
    payment_mode = models.CharField(max_length=20, choices=PAYMENT_MODES)
    reference_number = models.CharField(max_length=50, blank=True)
    proof_of_payment = models.ImageField(
        upload_to='payment_proofs/%Y/%m/%d/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])],
    )
    remarks = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='PENDING')
    received_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments_received')
    voided_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments_voided')
    void_reason = models.TextField(blank=True)
    void_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-payment_date', '-payment_time']

    def __str__(self):
        return f"{self.enrollment.student} - {self.amount} - {self.status}"

    def void_payment(self, user, reason=""):
        """Mark payment as voided"""
        if self.status == 'VOIDED':
            raise ValidationError('This payment is already voided')
        self.status = 'VOIDED'
        self.voided_by = user
        self.void_reason = reason
        self.void_date = timezone.now()
        self.save()

    def confirm_payment(self, user):
        """Mark payment as confirmed"""
        if self.status == 'CONFIRMED':
            raise ValidationError('This payment is already confirmed')
        self.status = 'CONFIRMED'
        self.received_by = user
        self.save()
        
        # Enrollment status becomes 'Fully Paid' if balance is 0, otherwise 'Enrolled'
        if self.enrollment.balance == 0:
            self.enrollment.status = 'Fully Paid'
        elif self.enrollment.status == 'Pending':
            self.enrollment.status = 'Enrolled'
        self.enrollment.save(update_fields=['status'])

class Concern(models.Model):
    STATUS_CHOICES = [
        ('Open', 'Open'),
        ('In Progress', 'In Progress'),
        ('Resolved', 'Resolved'),
        ('Closed', 'Closed'),
    ]
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='concerns')
    subject_text = models.CharField(max_length=200)
    description = models.TextField()
    date_filed = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Open')
    response = models.TextField(blank=True)
    date_responded = models.DateTimeField(null=True, blank=True)
    responded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='concerns_responded')
    date_resolved = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='concerns_resolved')
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-date_filed']

    def __str__(self):
        return f"{self.student} - {self.subject_text}"

    def resolve_concern(self, user, response=""):
        """Mark concern as resolved"""
        self.status = 'Resolved'
        self.response = response
        self.date_resolved = timezone.now()
        self.resolved_by = user
        self.save()

    def add_response(self, user, response):
        """Add response to concern"""
        self.status = 'In Progress'
        self.response = response
        self.date_responded = timezone.now()
        self.responded_by = user
        self.save()

# Teacher Model
class Teacher(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='teacher')
    employee_id = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    birthdate = models.DateField()
    gender = models.CharField(max_length=10)
    address = models.TextField()
    contact_number = models.CharField(max_length=20)
    photo = models.ImageField(upload_to='teacher_photos/', blank=True, null=True)
    status = models.CharField(max_length=20, default='Active', choices=[('Active', 'Active'), ('Inactive', 'Inactive')])
    subjects = models.ManyToManyField(
        'academics.Subject',
        blank=True,
        related_name='teachers',
    )

    class Meta:
        ordering = ['last_name', 'first_name']

    @property
    def full_name(self):
        if self.middle_name:
            return f"{self.first_name} {self.middle_name} {self.last_name}"
        return f"{self.first_name} {self.last_name}"

    @classmethod
    def generate_employee_id(cls):
        max_id = cls.objects.aggregate(max_id=Max('id'))['max_id'] or 0
        return f"{PROFESSOR_ID_PREFIX}{max_id + 1:04d}"

    def save(self, *args, **kwargs):
        if not self.employee_id:
            self.employee_id = self.generate_employee_id()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Teacher {self.full_name}"

# Signals to cleanup User when Profile is deleted
@receiver(post_delete, sender=Student)
def delete_user_with_student(sender, instance, **kwargs):
    if instance.user:
        try:
            instance.user.delete()
        except Exception:
            pass # Already deleted or doesn't exist

@receiver(post_delete, sender=Teacher)
def delete_user_with_teacher(sender, instance, **kwargs):
    if instance.user:
        try:
            instance.user.delete()
        except Exception:
            pass # Already deleted or doesn't exist
