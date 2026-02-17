from django.db import models
from django.utils.translation import gettext_lazy as _

class Ticket(models.Model):
    class Category(models.TextChoices):
        BILLING = 'billing', _('Billing')
        TECHNICAL = 'technical', _('Technical')
        ACCOUNT = 'account', _('Account')
        GENERAL = 'general', _('General')

    class Priority(models.TextChoices):
        LOW = 'low', _('Low')
        MEDIUM = 'medium', _('Medium')
        HIGH = 'high', _('High')
        CRITICAL = 'critical', _('Critical')

    class Status(models.TextChoices):
        OPEN = 'open', _('Open')
        IN_PROGRESS = 'in_progress', _('In Progress')
        RESOLVED = 'resolved', _('Resolved')
        CLOSED = 'closed', _('Closed')

    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(
        max_length=20,
        choices=Category.choices,
    )
    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.OPEN,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
