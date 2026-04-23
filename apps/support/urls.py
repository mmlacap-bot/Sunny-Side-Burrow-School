from django.urls import path
from . import views

urlpatterns = [
    path('student_concern/', views.student_concern, name='student_concern'),
    path('admin_portal_concerns/', views.admin_portal_concerns, name='admin_portal_concerns'),
    path('teacher_concerns/', views.teacher_concerns, name='teacher_concerns'),
    path('teacher_respond_concern/<int:concern_id>/', views.teacher_respond_concern, name='teacher_respond_concern'),
    path('admin_respond_concern/<int:concern_id>/', views.admin_respond_concern, name='admin_respond_concern'),
    path('admin_resolve_concern/<int:concern_id>/', views.admin_resolve_concern, name='admin_resolve_concern'),
    path('teacher_applications/', views.teacher_applications, name='teacher_applications'),

    # Inbox system (Direct Messaging)
    path('student_inbox/', views.student_inbox, name='student_inbox'),
    path('student_inbox/<int:thread_id>/', views.student_inbox, name='student_inbox_detail'),
    path('teacher_inbox/', views.teacher_inbox, name='teacher_inbox'),
    path('teacher_inbox/<int:thread_id>/', views.teacher_inbox, name='teacher_inbox_detail'),
    path('start_conversation/', views.start_conversation, name='start_conversation'),
    path('search_users/', views.search_users, name='search_users'),
]
