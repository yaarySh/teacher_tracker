from django.contrib.auth.models import AbstractUser
from django.db import models


class Teacher(AbstractUser):  # Now extending AbstractUser
    monthly_hours = models.PositiveIntegerField(default=0)

    REQUIRED_FIELDS = [
        "monthly_hours",
    ]  # Fields that are required for creating a superuser

    def __str__(self):
        return self.username  # Or you can return self.name if that's what you want


class DailyHourEntry(models.Model):
    # Foreign key to Teacher model
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    hours_added = models.PositiveIntegerField()

    class Meta:
        # Ensuring there is only one entry per teacher per day
        unique_together = ("teacher", "date")

    def __str__(self):
        return f"{self.teacher.username} - {self.date}: {self.hours_added} hours"
