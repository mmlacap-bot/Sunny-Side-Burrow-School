from django.db import models
from django.contrib.auth.models import AbstractUser


class RoleChoices(models.TextChoices):
    ADMIN = "ADMIN", "Administrator"
    TEACHER = "TEACHER", "Teacher"
    STUDENT = "STUDENT", "Student"
    REGISTRAR = "REGISTRAR", "Registrar"       # future-ready
    ACCOUNTING = "ACCOUNTING", "Accounting"    # future-ready


class User(AbstractUser):
    role = models.CharField(
        max_length=20,
        choices=RoleChoices.choices,
        default=RoleChoices.STUDENT
    )
    is_email_verified = models.BooleanField(default=False)
    
    # MFA Settings
    MFA_CHOICES = [
        ('NONE', 'None'),
        ('OTP', 'Email OTP'),
        ('QUESTION', 'Security Questions'),
    ]
    mfa_type = models.CharField(max_length=10, choices=MFA_CHOICES, default='NONE')
    
    # OTP Management
    last_otp = models.CharField(max_length=6, blank=True, null=True)
    otp_expiry = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['username']

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    def get_random_security_question(self):
        """Returns a random security question for this user"""
        return self.security_questions.order_by('?').first()


class SecurityQuestion(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='security_questions')
    question_text = models.CharField(max_length=255)
    hashed_answer = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def set_answer(self, answer):
        from django.contrib.auth.hashers import make_password
        self.hashed_answer = make_password(answer.lower().strip())

    def check_answer(self, answer):
        from django.contrib.auth.hashers import check_password
        if not self.hashed_answer:
            return False
        return check_password(answer.lower().strip(), self.hashed_answer)

    def __str__(self):
        return f"Question for {self.user.username}"
