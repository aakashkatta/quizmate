from django.shortcuts import render,redirect,get_object_or_404
from . import forms,models
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum
from django.contrib.auth.models import Group
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required,user_passes_test
from django.conf import settings
from exam import models as QMODEL
from teacher import models as TMODEL
from assignment.models import Assignment
import datetime
from django.urls import reverse
from django.db import transaction



#for showing signup/login button for student
def studentclick_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return render(request,'student/studentclick.html')

def student_signup_view(request):
    userForm=forms.StudentUserForm()
    studentForm=forms.StudentForm()
    mydict={'userForm':userForm,'studentForm':studentForm}
    if request.method=='POST':
        userForm=forms.StudentUserForm(request.POST)
        studentForm=forms.StudentForm(request.POST,request.FILES)
        if userForm.is_valid() and studentForm.is_valid():
            user=userForm.save()
            user.set_password(user.password)
            user.save()
            student=studentForm.save(commit=False)
            student.user=user
            student.save()
            my_student_group = Group.objects.get_or_create(name='STUDENT')
            my_student_group[0].user_set.add(user)
        return HttpResponseRedirect('studentlogin')
    return render(request,'student/studentsignup.html',context=mydict)

def is_student(user):
    return user.groups.filter(name='STUDENT').exists()

@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def student_dashboard_view(request):
    dict={
    
    'total_course':QMODEL.Course.objects.all().count(),
    'total_question':QMODEL.Question.objects.all().count(),
    'total_assignment' :Assignment.objects.count(),
    }
    return render(request,'student/student_dashboard.html',context=dict)

@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def student_exam_view(request):
    courses=QMODEL.Course.objects.all()
    return render(request,'student/student_exam.html',{'courses':courses})

@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def take_exam_view(request, pk):
    course = get_object_or_404(QMODEL.Course, id=pk)
    total_questions = QMODEL.Question.objects.filter(course=course).count()
    questions = QMODEL.Question.objects.filter(course=course)
    total_marks = questions.aggregate(total=Sum('marks'))['total'] or 0
    duration = course.duration  # Duration in minutes

    context = {
        'course': course,
        'total_questions': total_questions,
        'total_marks': total_marks,
        'duration': duration,
    }

    return render(request, 'student/take_exam.html', context)

# View to start an exam
@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def start_exam_view(request, pk):
    """
    View to start the exam. Checks if the student has already attempted the exam.
    """
    course = get_object_or_404(QMODEL.Course, id=pk)
    student = get_object_or_404(models.Student, user=request.user)
    
    # Check if the student has already attempted the exam
    if QMODEL.ExamAttempt.objects.filter(exam=course, student=student, completed=True).exists():
        messages.info(request, "You have already attempted this exam.")
        return redirect('view-result')
    
    questions = QMODEL.Question.objects.filter(course=course)
    duration = course.duration  # Duration in minutes
    
    # Create an ExamAttempt entry if not exists
    attempt, created = QMODEL.ExamAttempt.objects.get_or_create(student=student, exam=course)
    if not created and not attempt.completed:
        messages.info(request, "You have already started this exam.")
        return redirect('take-exam', pk=course.id)
    elif not created and attempt.completed:
        messages.info(request, "You have already attempted this exam.")
        return redirect('view-result')
    
    # Record the exam start time and duration in the session
    request.session['exam_start_time'] = timezone.now().isoformat()
    request.session['exam_duration'] = duration
    request.session['course_id'] = course.id  # Store course_id in session
    
    context = {
        'course': course,
        'questions': questions,
        'duration': duration,
    }
    
    return render(request, 'student/start_exam.html', context)

# View to calculate and record marks
@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def calculate_marks_view(request):
    """
    View to calculate and record the marks obtained by the student.
    """
    if request.method == 'POST':
        # Retrieve exam-related data from the session
        course_id = request.session.get('course_id')
        exam_start_time_iso = request.session.get('exam_start_time')
        exam_duration = request.session.get('exam_duration')  # Duration in minutes

        if not course_id or not exam_start_time_iso or not exam_duration:
            messages.error(request, "Exam session data is missing. Please try again.")
            return redirect('student-dashboard')

        try:
            # Fetch the course (exam) object
            course = QMODEL.Course.objects.get(id=course_id)
        except QMODEL.Course.DoesNotExist:
            messages.error(request, "Exam not found. Please contact support.")
            return redirect('student-dashboard')

        # Parse the exam start time
        try:
            exam_start_time = datetime.datetime.fromisoformat(exam_start_time_iso)
        except ValueError:
            messages.error(request, "Invalid exam start time format.")
            return redirect('student-dashboard')

        # Calculate the exam end time
        exam_end_time = exam_start_time + datetime.timedelta(minutes=exam_duration)
        current_time = timezone.now()

        # Optional: Check if the exam duration has been exceeded
        if current_time > exam_end_time:
            messages.warning(request, "You have exceeded the allotted time for this exam.")
            # You can choose to handle late submissions differently here

        # Proceed to calculate marks
        total_marks_obtained = 0
        questions = QMODEL.Question.objects.filter(course=course)

        for question in questions:
            # Retrieve the student's selected answer for each question
            selected_answer = request.POST.get(str(question.id))
            if selected_answer and selected_answer == question.answer:
                total_marks_obtained += question.marks

        # Record the exam attempt within a transaction to ensure data integrity
        try:
            with transaction.atomic():
                # Fetch the student profile
                student = models.Student.objects.get(user=request.user)

                # Fetch the active exam attempt
                exam_attempt = QMODEL.ExamAttempt.objects.get(
                    student=student,
                    exam=course,
                    completed=False
                )

                # Update the exam attempt with the obtained marks and mark it as completed
                exam_attempt.marks_obtained = total_marks_obtained
                exam_attempt.completed = True
                exam_attempt.submission_time = timezone.now()
                exam_attempt.save()
        except QMODEL.ExamAttempt.DoesNotExist:
            messages.error(request, "No active exam attempt found or you have already completed the exam.")
            return redirect('student-dashboard')
        except Exception as e:
            # Log the exception if needed
            messages.error(request, "An error occurred while processing your exam. Please contact support.")
            return redirect('student-dashboard')

        # Clear the exam-related session data
        for key in ['course_id', 'exam_start_time', 'exam_duration']:
            if key in request.session:
                del request.session[key]

        # Provide a success message with the obtained marks
        messages.success(request, f"Exam submitted successfully! Your score: {total_marks_obtained} / {course.total_marks}")

        # Redirect the student to the "My Marks" page
        return redirect('view-result')
    else:
        # If the request method is not POST, redirect to the student dashboard
        messages.error(request, "Invalid request method.")
        return redirect('student-dashboard')

# View to display all exam results
@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def view_result_view(request):
    """
    View to display all completed exam attempts and their results for the logged-in student.
    """
    student = get_object_or_404(models.Student, user=request.user)
    attempts = QMODEL.ExamAttempt.objects.filter(student=student, completed=True)
    
    context = {
        'attempts': attempts,
    }
    
    return render(request, 'student/view_result.html', context)

@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def check_marks_view(request,pk):
    course=QMODEL.Course.objects.get(id=pk)
    student = models.Student.objects.get(user_id=request.user.id)
    results= QMODEL.ExamAttempt.objects.all().filter(exam=course).filter(student=student)
    return render(request,'student/check_marks.html',{'results':results})

@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def student_marks_view(request):
    courses=QMODEL.Course.objects.all()
    return render(request,'student/student_marks.html',{'courses':courses})
  