from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User


class Category(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='categories',
        null=True,
        blank=True,
        db_index=True
    )
    name = models.CharField(max_length=50, db_index=True)
    color = models.CharField(max_length=7, default='#6366f1', help_text="Hex color code, e.g. #6366f1")
    icon = models.CharField(max_length=30, default='bookmark', help_text="Icon identifier")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']
        unique_together = ('user', 'name')

    def __str__(self):
        return self.name

    @property
    def active_tasks_count(self):
        return self.tasks.filter(completed=False).count()


class Task(models.Model):
    class Priority(models.TextChoices):
        LOW = 'LOW', 'Low'
        MEDIUM = 'MEDIUM', 'Medium'
        HIGH = 'HIGH', 'High'

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='tasks',
        null=True,
        blank=True,
        db_index=True
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    completed = models.BooleanField(default=False, db_index=True)
    priority = models.CharField(
        max_length=10,
        choices=Priority.choices,
        default=Priority.MEDIUM,
        db_index=True
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tasks',
        db_index=True
    )
    due_date = models.DateField(null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['completed', '-priority', 'due_date', '-created_at']
        indexes = [
            models.Index(fields=['user', 'completed', 'due_date']),
            models.Index(fields=['user', 'completed', 'priority']),
        ]

    def __str__(self):
        return self.title

    @property
    def is_overdue(self):
        if self.due_date and not self.completed:
            return self.due_date < timezone.now().date()
        return False

    @property
    def is_due_today(self):
        if self.due_date and not self.completed:
            return self.due_date == timezone.now().date()
        return False

    @property
    def subtasks_total_count(self):
        return self.subtasks.count()

    @property
    def subtasks_completed_count(self):
        return self.subtasks.filter(is_completed=True).count()

    @property
    def progress_percentage(self):
        total = self.subtasks_total_count
        if total == 0:
            return 100 if self.completed else 0
        return int((self.subtasks_completed_count / total) * 100)


class SubTask(models.Model):
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='subtasks',
        db_index=True
    )
    title = models.CharField(max_length=255)
    is_completed = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['is_completed', 'created_at']

    def __str__(self):
        return f"{self.task.title} - {self.title}"
