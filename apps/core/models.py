from django.db import models


class BaseModel(models.Model):
    """
    Abstract base model for all domain models.
    Provides automatic timestamp tracking.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
