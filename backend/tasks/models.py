from django.db import models

class Task(models.Model):
    title = models.CharField(max_length=255)
    due_date = models.DateField(null=True, blank=True)
    estimated_hours = models.FloatField(default=1.0)
    importance = models.IntegerField(default=5)
    # store dependencies as comma-separated IDs for simplicity if persisted
    dependencies = models.JSONField(default=list, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.id} - {self.title}"
