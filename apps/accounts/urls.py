from django.urls import path
from django.views.generic import RedirectView
from . import views

urlpatterns = [
    path('logout/', views.logout_view, name='logout'),
    path('forgot_password/', views.forgot_password, name='forgot_password'),
    path('login/', RedirectView.as_view(url='/', permanent=False), name='login'),
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('account_details/', views.account_details, name='account_details'),
    path('change_password/', views.change_password, name='change_password'),
    path('settings/', views.settings_view, name='settings'),
    path('mfa_verify/', views.mfa_verify, name='mfa_verify'),
    path('mfa_question/', views.mfa_question, name='mfa_question'),
]

