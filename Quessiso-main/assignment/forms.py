# assignments/forms.py

from django import forms
from .models import Assignment, Submission
from django.core.exceptions import ValidationError
import os  # For file extension handling

class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ['title', 'description', 'due_date', 'required_keywords','course','marks']  # Removed 'file'
        widgets = {
            'due_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'required_keywords': forms.TextInput(attrs={
                'placeholder': 'e.g., introduction, conclusion',
                'class': 'form-control'
            }),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'course': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Course Name'}),
            'marks': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class SubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ['file']
        widgets = {
            'file': forms.ClearableFileInput(attrs={'accept': '.pdf,.docx', 'class': 'form-control-file'}),
        }

    def clean_file(self):
        file = self.cleaned_data.get('file', False)
        if file:
            # Check file size (limit to 5MB)
            if file.size > 5 * 1024 * 1024:
                raise ValidationError("File size must be under 5MB.")
            
            # Validate file extension
            ext = os.path.splitext(file.name)[1].lower()
            if ext not in ['.pdf', '.docx']:
                raise ValidationError("Unsupported file extension. Please upload a PDF or DOCX file.")
            
            return file
        else:
            raise ValidationError("Couldn't read uploaded file.")
