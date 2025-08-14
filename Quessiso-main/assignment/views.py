import os
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponseRedirect
from django.utils import timezone
from .models import Assignment, Submission
from .forms import AssignmentForm, SubmissionForm
from .utils import validate_submission
from student.models import Student

# Helper functions to check user roles
def is_admin(user):
    return user.is_superuser

def is_teacher(user):
    return user.groups.filter(name='TEACHER').exists()

def is_student(user):
    return not user.is_staff and not user.is_superuser

# -----------------------
# Admin Views
# -----------------------

@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_assignment_view(request):
    """
    Display the admin's assignment dashboard.
    """
    return render(request, 'exam/admin_assignment.html')

@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_add_assignment_view(request):
    """
    Allows admins to create a new assignment.
    """
    if request.method == 'POST':
        form = AssignmentForm(request.POST, request.FILES)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.created_by = request.user
            assignment.save()
            messages.success(request, "Assignment added successfully!")
            return redirect('admin-view-assignment')
        else:
            messages.error(request, "There was an error adding the assignment. Please check the form.")
    else:
        form = AssignmentForm()
    return render(request, 'exam/admin_add_assignment.html', {'form': form})

@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_view_assignment_view(request):
    assignments = Assignment.objects.all().order_by('-created_at')
    return render(request, 'exam/admin_view_assignment.html',{'assignments': assignments})

@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_delete_assignment_view(request, pk):
    """
    Allows admins to delete an assignment.
    """
    try:
        assignment = get_object_or_404(Assignment, id=pk, created_by=request.user)
        print(assignment)  # Debug: Check if the assignment is being retrieved correctly
        assignment.delete()
        messages.success(request, "Assignment deleted successfully!")
    except Exception as e:
        print(f"Error: {e}")  # Debug any potential errors
    return redirect('admin-view-assignment')

@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_view_student_grades_view(request):
    """
    Lists all students for viewing assignment marks.
    """
    students = Student.objects.all()
    return render(request, 'exam/admin_view_student_grades.html', {'students': students})


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_view_grades_view(request, pk):
    """
    Lists all assignments for a selected student to view marks.
    """
    assignments = Assignment.objects.all()
    response = render(request, 'exam/admin_view_submissions.html', {'assignments': assignments})
    response.set_cookie('student_id', str(pk))  # Store student ID in cookie
    return response


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_check_grades_view(request, pk):
    """
    Displays marks for a specific assignment for a selected student.
    """
    assignment = get_object_or_404(Assignment, id=pk)
    student_id = request.COOKIES.get('student_id')
    
    # Retrieve the Student instance
    student = get_object_or_404(Student, id=student_id)

    # Retrieve the associated User instance if Submission model references User instead of Student
    user_instance = student.user  # Adjust this if Student model has a related User field named `user`

    # Fetch results related to the specific assignment and student (or user if required)
    results = Submission.objects.filter(assignment=assignment, student=user_instance)
    
    return render(request, 'exam/admin_check_grades.html', {'results': results})

# -----------------------
# Teacher Views
# -----------------------

@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
def teacher_assignment_view(request):
    return render(request, 'teacher/teacher_assignment.html')


@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
def teacher_add_assignment_view(request):
    """
    Allows teachers to create a new assignment.
    """
    if request.method == 'POST':
        form = AssignmentForm(request.POST, request.FILES)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.created_by = request.user
            assignment.save()
            messages.success(request, "Assignment added successfully!")
            return redirect('teacher:teacher-view-assignment')
        else:
            messages.error(request, "There was an error adding the assignment. Please check the form.")
    else:
        form = AssignmentForm()
    return render(request, 'teacher/teacher_add_assignment.html', {'form': form})

@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
def teacher_view_assignment_view(request):
    """
    Displays all assignments created by the teacher.
    """
    assignments = Assignment.objects.filter(created_by=request.user).order_by('-created_at')
    print(assignments)
    return render(request, 'teacher/teacher_view_assignment.html', {'assignments': assignments})

@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)

def teacher_delete_assignment_view(request, pk):
    """
    Allows teachers to delete an assignment.
    """
    try:
        assignment = get_object_or_404(Assignment, id=pk, created_by=request.user)
        print(assignment)  # Debug: Check if the assignment is being retrieved correctly
        assignment.delete()
        messages.success(request, "Assignment deleted successfully!")
    except Exception as e:
        print(f"Error: {e}")  # Debug any potential errors
    return redirect('teacher:teacher-view-assignment')


@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
def teacher_view_submissions_view(request):
    """
    Allows teachers to view submissions for their assignments.
    """
    submissions = Submission.objects.filter(assignment__created_by=request.user).order_by('-submitted_at')
    return render(request, 'teacher/teacher_view_submissions.html', {'submissions': submissions})

# -----------------------
# Student Views
# -----------------------

@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def student_assignment_view(request):
    """
    Displays all available assignments for the student.
    If the due date has passed for an assignment, the student will not be able to access it.
    """
    now = timezone.now()
    assignments = Assignment.objects.filter(due_date__gte=now).order_by('-created_at')

    # Fetch assignments that are still available (due date not passed)
    return render(request, 'student/student_assignment.html', {'assignments': assignments})
@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def upload_submission_view(request, pk):
    """
    Allows students to upload a submission for a specific assignment.
    If the due date has passed, they will be informed that the due date has passed, 
    and they can no longer submit. Students can only resubmit if their submission fails
    due to invalid file format or insufficient word count.
    """
    assignment = get_object_or_404(Assignment, id=pk)
    student = request.user
    now = timezone.now()

    # Check if the due date has passed
    if assignment.due_date < now:
        messages.error(request, "The due date for this assignment has passed. You cannot submit now.")
        return redirect('student-assignment-view')

    # Check if the student has already submitted this assignment
    submission = Submission.objects.filter(student=student, assignment=assignment).first()
    if submission and submission.grade is not None and submission.grade > 0:
        messages.info(request, "You have already submitted this assignment and received a grade.")
        return redirect('view-assignment-results')

    if request.method == 'POST':
        form = SubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            # Handle new or resubmission case
            file = form.cleaned_data['file']
            if submission:
                submission.file = file
                submission.submitted_at = timezone.now()
            else:
                submission = form.save(commit=False)
                submission.student = student
                submission.assignment = assignment

            submission.save()

            # Perform validation and grading
            file_path = submission.file.path
            grade, feedback = validate_submission(file_path, assignment)

            submission.grade = grade
            submission.feedback = feedback
            submission.save()

            print(f"DEBUG: Grade = {grade}, Feedback = {feedback}")

            # Allow resubmission only if file format or word count is insufficient
            if grade <= 1.0:
                messages.error(request, f"Assignment validation failed: {feedback}")
                Submission.objects.filter(student=student, assignment=assignment).delete()
                return render(request, 'student/upload_submission.html', {'form': form, 'assignment': assignment})

            messages.success(request, f"Assignment submitted and graded successfully! Grade: {grade}/5")
            return redirect('student-assignment-view')
        else:
            messages.error(request, "There was an error uploading the assignment.")
    else:
        form = SubmissionForm()

    return render(request, 'student/upload_submission.html', {'form': form, 'assignment': assignment})
@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def check_submission_view(request, pk):
    """
    Allows students to view their submitted assignments along with grades and feedback for a specific course or assignment.
    """
    student = request.user
    # Assuming pk refers to a specific assignment or course
    submissions = Submission.objects.filter(student=student, assignment__id=pk).order_by('-submitted_at')
    return render(request, 'student/check_submission.html', {'submissions': submissions})
@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def my_marks_view(request):
    student = request.user  
    submissions = Submission.objects.filter(student=student).order_by('-submitted_at')  # For assignment submissions

    context = {
        'submissions': submissions
    }
    return render(request, 'student/student_grades.html', context)
@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def view_assignment_results(request):
    """
    View to display all completed assignment submissions and their results for the logged-in student.
    """
    # Retrieve the logged-in student's submission records for assignments
    student =request.user
    assignment =Submission.objects.filter(student=student).select_related('assignment').order_by('-submitted_at').first()


    context = {
        'assignment': assignment
    }
    return render(request, 'student/view_aresult.html', context)
