from django.db import models
from django.conf import settings


# ============================================================================
# NEW CORE MESSAGING (User ↔ User)
# ============================================================================

class DirectThread(models.Model):
    """
    1-to-1 thread between two Users.
    We store both user FKs + a uniqueness constraint to guarantee one thread per pair.
    """

    user1 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='direct_threads_as_user1',
    )
    user2 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='direct_threads_as_user2',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user1', 'user2'], name='unique_direct_thread_pair'),
        ]
        ordering = ['-updated_at']

    def __str__(self):
        return f"DirectThread {self.user1_id}↔{self.user2_id}"


class MessageStatus(models.TextChoices):
    SENT = "SENT", "Sent"
    READ = "READ", "Read"


class DirectMessage(models.Model):
    thread = models.ForeignKey(
        DirectThread,
        on_delete=models.CASCADE,
        related_name='messages',
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='direct_messages_sent',
    )
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='direct_messages_received',
    )
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=MessageStatus.choices, default=MessageStatus.SENT)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"DirectMessage {self.id} ({self.status})"


# ============================================================================
# LEGACY (Student ↔ Teacher only) — kept to avoid breaking old data
# ============================================================================

class MessageThread(models.Model):
    student = models.ForeignKey(
        'student.Student',
        on_delete=models.CASCADE,
        related_name='message_threads',
    )
    teacher = models.ForeignKey(
        'student.Teacher',
        on_delete=models.CASCADE,
        related_name='message_threads',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['student', 'teacher'],
                name='unique_student_teacher_thread',
            ),
        ]
        ordering = ['-updated_at']

    def __str__(self):
        return f"Thread: {self.student} ↔ {self.teacher}"


class Message(models.Model):
    thread = models.ForeignKey(
        MessageThread,
        on_delete=models.CASCADE,
        related_name='messages',
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages',
    )
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    read_by_student = models.BooleanField(default=False)
    read_by_teacher = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']


