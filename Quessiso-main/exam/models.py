# models.py
from django.db import models
from student.models import Student

class Course(models.Model):
    course_name = models.CharField(max_length=50)
    question_number = models.PositiveIntegerField()
    total_marks = models.PositiveIntegerField()
    duration = models.PositiveIntegerField(help_text="Duration of the exam in minutes",default=30)  # New Field

    def __str__(self):
        return self.course_name

class Question(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='questions')
    marks = models.PositiveIntegerField()
    question = models.CharField(max_length=600)
    option1 = models.CharField(max_length=200)
    option2 = models.CharField(max_length=200)
    option3 = models.CharField(max_length=200)
    option4 = models.CharField(max_length=200)
    CAT_CHOICES = (
        ('Option1', 'Option1'),
        ('Option2', 'Option2'),
        ('Option3', 'Option3'),
        ('Option4', 'Option4'),
    )
    answer = models.CharField(max_length=200, choices=CAT_CHOICES)

    def __str__(self):
        return self.question

class ExamAttempt(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='exam_attempts')
    exam = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='attempts')
    attempt_time = models.DateTimeField(auto_now_add=True)
    completed = models.BooleanField(default=False)
    marks_obtained = models.PositiveIntegerField(null=True, blank=True)
    submission_time = models.DateTimeField(null=True, blank=True)  # Optional: Track submission time

    class Meta:
        unique_together = ('student', 'exam')  # Ensures one attempt per student per exam

    def __str__(self):
        status = 'Completed' if self.completed else 'In Progress'
        return f"{self.student} - {self.exam} - {status}"
