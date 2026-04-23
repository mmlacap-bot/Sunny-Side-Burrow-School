from django.urls import path
from . import views

urlpatterns = [
    path('student_enrollment/', views.student_enrollment, name='student_enrollment'),
    path('api/get_sections_by_grade_level/', views.get_sections_by_grade_level, name='get_sections_by_grade_level'),
    path('api/get_schedule_by_section/', views.get_schedule_by_section, name='get_schedule_by_section'),
    path('admin_create_enrollment/', views.admin_create_enrollment, name='admin_create_enrollment'),
    path('admin_update_enrollment/<int:enrollment_id>/', views.admin_update_enrollment, name='admin_update_enrollment'),
    path('cancel_enrollment/<int:enrollment_id>/', views.cancel_enrollment, name='cancel_enrollment'),
]
