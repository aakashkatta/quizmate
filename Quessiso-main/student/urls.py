from django.urls import path
from student import views
from django.contrib.auth.views import LoginView
from assignment import views as assignment_views
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
path('studentclick', views.studentclick_view),
path('studentlogin', LoginView.as_view(template_name='student/studentlogin.html'),name='studentlogin'),
path('studentsignup', views.student_signup_view,name='studentsignup'),
path('student-dashboard', views.student_dashboard_view,name='student-dashboard'),
path('student-exam', views.student_exam_view,name='student-exam'),
path('take-exam/<int:pk>', views.take_exam_view,name='take-exam'),
path('start-exam/<int:pk>', views.start_exam_view,name='start-exam'),

path('calculate-marks', views.calculate_marks_view,name='calculate-marks'),
path('view-result', views.view_result_view,name='view-result'),
path('check-marks/<int:pk>', views.check_marks_view,name='check-marks'),
path('student-marks', views.student_marks_view,name='student-marks'),

path('student-assignment', assignment_views.student_assignment_view, name='student-assignment-view'),
path('student-submit/<int:pk>/', assignment_views.upload_submission_view, name='upload-submission'),
path('student-submissions/<int:pk>/', assignment_views.check_submission_view, name='check-submission'),
path('student-grades',assignment_views.my_marks_view,name='student-grades'),
path('view-assignment-results',assignment_views.view_assignment_results, name='view-assignment-results'),
]
