from django.urls import path
from . import views

urlpatterns = [
    path('admin_manage_school_year/', views.admin_manage_school_year, name='admin_manage_school_year'),
    path('admin_manage_school_year/<int:year_id>/', views.admin_manage_school_year, name='admin_manage_school_year_edit'),
    path('admin_manage_grade_level/', views.admin_manage_grade_level, name='admin_manage_grade_level'),
    path('admin_manage_grade_level/<int:grade_id>/', views.admin_manage_grade_level, name='admin_manage_grade_level_edit'),
    path('admin_manage_section/', views.admin_manage_section, name='admin_manage_section'),
    path('admin_manage_section/<int:section_id>/', views.admin_manage_section, name='admin_manage_section_edit'),
    path('admin_manage_subject/', views.admin_manage_subject, name='admin_manage_subject'),
    path('admin_manage_subject/<int:subject_id>/', views.admin_manage_subject, name='admin_manage_subject_edit'),
    path('admin_manage_schedule/', views.admin_manage_schedule, name='admin_manage_schedule'),
    path('admin_manage_schedule/<int:schedule_id>/', views.admin_manage_schedule, name='admin_manage_schedule_edit'),
]
