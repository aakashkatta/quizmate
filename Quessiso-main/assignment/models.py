# assignments/models.py

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone 
import os
from django.conf import settings
from django.db.models.signals import pre_delete
from django.dispatch import receiver


class Assignment(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    due_date = models.DateTimeField()
    required_keywords = models.CharField(
        max_length=255,
        help_text="Enter required keywords separated by commas (e.g., introduction, conclusion)"
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='assignments'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    course = models.CharField(max_length=100, null=True, blank=True)  
    marks = models.IntegerField(default=5)

    def __str__(self):
        return self.title

    def get_required_keywords_list(self):
        """
        Returns a list of required keywords.
        """
        return [kw.strip().lower() for kw in self.required_keywords.split(',') if kw.strip()]

class Submission(models.Model):
    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
        related_name='submissions'
    )
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='submissions'
    )
    
    file = models.FileField(upload_to='submissions/')
    submitted_at = models.DateTimeField(auto_now_add=True)
    grade = models.FloatField(null=True, blank=True)
    feedback = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.assignment.title} - {self.student.username}"
    
    def delete(self, *args, **kwargs):
        # Delete the file from the filesystem
        if self.file:
            if os.path.isfile(self.file.path):
                os.remove(self.file.path)
        # Call the superclass delete() to remove the instance
        super().delete(*args, **kwargs)
    
    @receiver(pre_delete, sender=Assignment)
    def delete_related_submissions(sender, instance, **kwargs):
    # Delete all submissions related to the assignment
        for submission in instance.submissions.all():
            submission.delete()
