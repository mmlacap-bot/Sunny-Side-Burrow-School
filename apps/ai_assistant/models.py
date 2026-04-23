from django.db import models


class AIRequestLog(models.Model):
    teacher = models.ForeignKey(
        'student.Teacher',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ai_requests'
    )
    question = models.TextField()
    response = models.TextField(blank=True)
    tokens_used = models.IntegerField(default=0)
    response_time_seconds = models.FloatField(default=0)
    was_successful = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"AI request by {self.teacher or 'Unknown'} on {self.created_at:%Y-%m-%d %H:%M:%S}" 
