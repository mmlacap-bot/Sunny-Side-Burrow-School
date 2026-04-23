from django.contrib import admin

from .models import (
    Concern,
    Enrollment,
    EnrollmentSubject,
    Payment,
    Teacher,
    Student,
)


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'first_name', 'last_name', 'login_email')
    readonly_fields = ('login_email', 'contact_email')
    
    fieldsets = (
        ('Student Information', {
            'fields': ('student_id', 'first_name', 'last_name', 'middle_name', 'birthdate', 'gender', 'address', 'contact_number', 'photo')
        }),
        ('Guardian Information', {
            'fields': ('guardian_name', 'guardian_contact')
        }),
        ('Account Information', {
            'fields': ('user', 'login_email', 'contact_email')
        }),
    )

    @admin.display(description='Registered Login Email')
    def login_email(self, obj):
        return obj.user.username if obj.user else "-"

    @admin.display(description='Contact Email')
    def contact_email(self, obj):
        return obj.user.email if obj.user else "-"

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'school_year', 'grade_level', 'section', 'status')

@admin.register(EnrollmentSubject)
class EnrollmentSubjectAdmin(admin.ModelAdmin):
    list_display = ('enrollment', 'class_schedule', 'status')

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('enrollment', 'amount', 'payment_date', 'payment_mode')

@admin.register(Concern)
class ConcernAdmin(admin.ModelAdmin):
    list_display = ('student', 'subject_text', 'status', 'date_filed')


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('employee_id', 'display_full_name', 'status', 'login_email')
    search_fields = ('employee_id', 'first_name', 'last_name')
    list_filter = ('status',)
    ordering = ('last_name', 'first_name')
    readonly_fields = ('employee_id', 'login_email', 'contact_email')

    fieldsets = (
        ('Teacher Information', {
            'fields': ('employee_id', 'first_name', 'last_name', 'middle_name', 'birthdate', 'gender', 'address', 'contact_number', 'photo', 'status')
        }),
        ('Account Information', {
            'fields': ('user', 'login_email', 'contact_email')
        }),
    )

    @admin.display(description='Registered Login Email')
    def login_email(self, obj):
        return obj.user.username if obj.user else "-"

    @admin.display(description='Contact Email')
    def contact_email(self, obj):
        return obj.user.email if obj.user else "-"

    @admin.display(description='Full name')
    def display_full_name(self, obj):
        return obj.full_name
