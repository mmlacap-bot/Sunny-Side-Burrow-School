from django.urls import path
from . import views

urlpatterns = [
    path('student_payment/', views.student_payment, name='student_payment'),
    path('admin_portal_payment/', views.admin_portal_payment, name='admin_portal_payment'),
    path('admin_process_payment/<int:enrollment_id>/', views.admin_process_payment, name='admin_process_payment'),
    path('admin_confirm_payment/<int:payment_id>/', views.admin_confirm_payment, name='admin_confirm_payment'),
    path('admin_void_payment/<int:payment_id>/', views.admin_void_payment, name='admin_void_payment'),
]
