from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView
from . import views
from apps.ai_assistant import views as ai_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.accounts.urls')),
    path('', include('apps.academics.urls')),
    path('', include('apps.enrollment.urls')),
    path('', include('apps.finance.urls')),
    path('', include('apps.support.urls')),
    path('about/', views.about, name='about'),
    
    # Student views
    path('student_dashboard/', views.student_dashboard, name='student_dashboard'),
    path('student_schedule/', views.student_schedule, name='student_schedule'),
    path('student_people/', views.student_people, name='student_people'),

    # Teacher views (Phase 2 & 3)
    path('teacher_dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher_profile/', views.teacher_profile, name='teacher_profile'),
    path('teacher_schedule/', views.teacher_schedule, name='teacher_schedule'),
    path('teacher_sections/', views.teacher_sections, name='teacher_sections'),
    path('teacher_adviser_setup/', views.teacher_adviser_setup, name='teacher_adviser_setup'),
    path('teacher_ai_assistance/', ai_views.teacher_ai_assistance, name='teacher_ai_assistance'),

    # Admin Registration (Phase 2)
    path('admin_register_teacher/', views.admin_register_teacher, name='admin_register_teacher'),
    path('admin_register_student/', views.admin_register_student, name='admin_register_student'),

    # Admin Portal - Dashboard & Main Views
    path('admin_portal_dashboard/', views.admin_portal_dashboard, name='admin_portal_dashboard'),
    path('admin_portal_students/', views.admin_portal_students, name='admin_portal_students'),
    path('admin_delete_student/<int:pk>/', views.admin_delete_student, name='admin_delete_student'),
    path('admin_portal_enrollment/', views.admin_portal_enrollment, name='admin_portal_enrollment'),
    path('admin_portal_sections/', views.admin_portal_sections, name='admin_portal_sections'),
    path('admin_portal_subjects/', views.admin_portal_subjects, name='admin_portal_subjects'),
    path('admin_portal_schedule/', views.admin_portal_schedule, name='admin_portal_schedule'),
    path('admin_portal_school_year/', views.admin_portal_school_year, name='admin_portal_school_year'),
    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) \
  + static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
