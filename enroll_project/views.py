import datetime
import random

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie

from apps.accounts.forms import LoginForm, TeacherRegistrationForm, StudentPhotoForm, StudentRegistrationForm
from apps.enrollment.forms import EnrollmentForm
from apps.support.forms import ConcernForm
from apps.student.models import (
    Concern,
    Enrollment,
    EnrollmentSubject,
    Payment,
    Teacher,
    Student,
)
from apps.academics.models import (
    ClassSchedule,
    GradeLevel,
    SchoolYear,
    Section,
    Subject,
)

User = get_user_model()
staff_required = user_passes_test(lambda u: u.is_staff)


def normalize_for_email(value):
    return ''.join(ch.lower() for ch in value if ch.isalnum())


def generate_email(first_name, last_name):
    base_first = normalize_for_email(first_name) or 'user'
    base_last = normalize_for_email(last_name)
    local_part = f"{base_first}.{base_last}" if base_last else base_first
    for _ in range(20):
        login_email = f"{local_part}{random.randint(100, 999)}@sunnyday.edu.ph"
        if not User.objects.filter(username__iexact=login_email).exists():
            return login_email
    suffix = 1
    while True:
        login_email = f"{local_part}{suffix:03d}@sunnyday.edu.ph"
        if not User.objects.filter(username__iexact=login_email).exists():
            return login_email
        suffix += 1
        suffix += 1


def ensure_enrollment_reference_data():
    active_year = SchoolYear.objects.filter(is_active=True).first()
    if not active_year:
        active_year = SchoolYear.objects.create(year_start=2025, year_end=2026, is_active=True)

    grade_levels = {}
    grade_level_defs = [
        ('Kinder', 1),
        ('Preparatory', 2),
        ('Grade 1', 3),
        ('Grade 2', 4),
        ('Grade 3', 5),
        ('Grade 4', 6),
        ('Grade 5', 7),
        ('Grade 6', 8),
    ]

    # Ensure each grade level exists and has the desired order.
    for name, order in grade_level_defs:
        grade_level, created = GradeLevel.objects.get_or_create(name=name, defaults={'level_order': order})
        if not created and grade_level.level_order != order:
            grade_level.level_order = order
            grade_level.save(update_fields=['level_order'])
        grade_levels[name] = grade_level

    # Merge duplicate grade levels and preserve related objects.
    for name, order in grade_level_defs:
        duplicates = GradeLevel.objects.filter(name=name).order_by('level_order', 'id')
        if duplicates.count() > 1:
            primary = duplicates.first()
            if primary.level_order != order:
                primary.level_order = order
                primary.save(update_fields=['level_order'])
            for duplicate in duplicates[1:]:
                Section.objects.filter(grade_level=duplicate).update(grade_level=primary)
                Subject.objects.filter(grade_level=duplicate).update(grade_level=primary)
                Enrollment.objects.filter(grade_level=duplicate).update(grade_level=primary)
                duplicate.delete()
            grade_levels[name] = primary

    # Remove legacy combined grade levels if they still exist.
    for old_name in ['Kinder & Preparatory', 'Grade 4-6', 'Grade 1-2']:
        for old_grade in GradeLevel.objects.filter(name=old_name):
            Section.objects.filter(grade_level=old_grade).delete()
            Subject.objects.filter(grade_level=old_grade).delete()
            Enrollment.objects.filter(grade_level=old_grade).update(grade_level=grade_levels.get('Grade 1', old_grade))
            old_grade.delete()

    sections = {}
    section_names = ['A', 'B']
    for grade_name, grade_level in grade_levels.items():
        for section_name in section_names:
            # Set limits: Kinder/Prep = 15, Grade 1-6 = 25
            if grade_name in ['Kinder', 'Preparatory']:
                max_students = 15
            else:
                max_students = 25
                
            sections[(grade_name, section_name)], _ = Section.objects.get_or_create(
                name=section_name,
                grade_level=grade_level,
                school_year=active_year,
                defaults={'max_students': max_students},
            )
            # Ensure existing sections are updated to the new limits
            Section.objects.filter(grade_level=grade_level, name=section_name).update(max_students=max_students)

    subjects_by_grade = {
        'Kinder': ['Math', 'Science', 'English', 'Filipino', 'CL', 'Recess'],
        'Preparatory': ['Math', 'Science', 'English', 'Filipino', 'CL', 'Recess'],
        'Grade 1': ['Math', 'English', 'Filipino', 'Makabansa', 'CL', 'MAPE', 'Recess'],
        'Grade 2': ['Math', 'English', 'Filipino', 'Makabansa', 'CL', 'MAPE', 'Recess'],
        'Grade 3': ['Math', 'English', 'Filipino', 'CL', 'MAPE', 'Makabansa', 'Recess'],
        'Grade 4': ['Math', 'English', 'Science', 'CL', 'MAPE', 'HELE', 'AP', 'Computer', 'Recess'],
        'Grade 5': ['Math', 'English', 'Science', 'CL', 'MAPE', 'HELE', 'AP', 'Computer', 'Recess'],
        'Grade 6': ['Math', 'English', 'Science', 'CL', 'MAPE', 'HELE', 'AP', 'Computer', 'Recess'],
    }

    for grade_name, subject_names in subjects_by_grade.items():
        grade_level = grade_levels[grade_name]
        for idx, subject_name in enumerate(subject_names, start=1):
            code = f"{grade_level.level_order:02d}{idx:02d}"
            subject, _ = Subject.objects.get_or_create(
                code=code,
                grade_level=grade_level,
                defaults={'name': subject_name, 'units': 1.0, 'description': ''},
            )
            if subject.name != subject_name:
                subject.name = subject_name
                subject.save(update_fields=['name'])

    for (grade_name, section_name), section in sections.items():
        grade_level = grade_levels[grade_name]
        subjects = Subject.objects.filter(grade_level=grade_level).order_by('code')
        
        # Room Calculation Logic
        base_char = chr(64 + grade_level.level_order)
        room_suffix = "001" if section.name == 'A' else "002"
        main_room = f"{base_char}{room_suffix}"

        for idx, subject in enumerate(subjects):
            day_cycle = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
            day = day_cycle[idx % len(day_cycle)]
            start_hour = 8 + (idx % 8)
            end_hour = start_hour + 1
            
            # Special case for Recess
            is_recess = subject.name.lower() == 'recess'
            if is_recess and day == 'Sat':
                day = 'Fri' # Move Saturday recess to Friday
                
            current_room = 'School Canteen' if is_recess else main_room
            
            ClassSchedule.objects.get_or_create(
                subject=subject,
                section=section,
                school_year=active_year,
                defaults={
                    'day': day,
                    'time_start': datetime.time(start_hour, 0),
                    'time_end': datetime.time(end_hour, 0),
                    'room': current_room,
                    'teacher': None,
                },
            )






@login_required
def student_dashboard(request):
    try:
        student = request.user.student
    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found. Please contact administrator.')
        return redirect('home')

    if request.method == 'POST':
        if request.POST.get('remove_photo'):
            if student.photo:
                student.photo.delete(save=False)
                student.photo = None
                student.save()
            messages.success(request, 'Profile photo removed.')
            return redirect('student_dashboard')
        photo_form = StudentPhotoForm(request.POST, request.FILES, instance=student)
        if photo_form.is_valid():
            if request.FILES.get('photo'):
                photo_form.save()
                messages.success(request, 'Profile photo updated.')
            return redirect('student_dashboard')
    else:
        photo_form = StudentPhotoForm(instance=student)

    enrollment = Enrollment.objects.filter(student=student, school_year__is_active=True).first()
    subjects = []
    if enrollment:
        if enrollment.status == 'Pending' and enrollment.payment_status == 'Paid':
            enrollment.status = 'Enrolled'
            enrollment.save(update_fields=['status'])
        subjects = EnrollmentSubject.objects.filter(enrollment=enrollment).select_related('class_schedule__subject')
    return render(
        request,
        'accounts/student_dashboard.html',
        {
            'student': student,
            'enrollment': enrollment,
            'subjects': subjects,
            'photo_form': photo_form,
        },
    )


@login_required
@staff_required
def teacher_dashboard(request):
    try:
        teacher = request.user.teacher
    except Teacher.DoesNotExist:
        messages.error(request, 'Teacher profile not found.')
        return redirect('home')

    current_year = SchoolYear.objects.filter(is_active=True).first()
    schedules = ClassSchedule.objects.filter(teacher=teacher, school_year=current_year).select_related('subject', 'section') if current_year else ClassSchedule.objects.none()
    sections = Section.objects.filter(schedules__teacher=teacher, schedules__school_year=current_year).distinct() if current_year else Section.objects.none()
    student_ids = Enrollment.objects.filter(section__in=sections).values_list('student_id', flat=True)
    concern_count = Concern.objects.filter(student__id__in=student_ids).count() if student_ids else 0

    return render(request, 'accounts/teacher_dashboard.html', {
        'teacher': teacher,
        'schedules': schedules,
        'schedule_count': schedules.count(),
        'section_count': sections.count(),
        'concern_count': concern_count,
        'active_page': 'dashboard',
    })




@login_required
def student_schedule(request):
    try:
        student = request.user.student
    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found. Please contact administrator.')
        return redirect('home')

    # Status must be 'Enrolled' as per user requirement (don't show for Pending)
    enrollment = Enrollment.objects.filter(
        student=student, 
        school_year__is_active=True,
        status='Enrolled'
    ).first()
    
    schedules = []
    if enrollment:
        schedules = ClassSchedule.objects.filter(
            section=enrollment.section,
            school_year=enrollment.school_year
        ).select_related('subject', 'section').order_by('time_start')

    time_slots = ['08:00', '09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00']
    days = [('Mon', 'Monday'), ('Tue', 'Tuesday'), ('Wed', 'Wednesday'), ('Thu', 'Thursday'), ('Fri', 'Friday'), ('Sat', 'Saturday')]
    
    return render(request, 'accounts/student_schedule.html', {
        'enrollment': enrollment,
        'schedules': schedules, 
        'time_slots': time_slots, 
        'days': days
    })


@login_required
def student_people(request):
    try:
        student = request.user.student
    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found. Please contact administrator.')
        return redirect('home')

    enrollment = (
        Enrollment.objects.filter(
            student=student,
            school_year__is_active=True,
            status__in=['Pending', 'Enrolled'],
        )
        .select_related('section__grade_level', 'section__school_year', 'section__teacher__user')
        .first()
    )

    adviser = None
    classmates = Student.objects.none()
    section = None

    if enrollment and enrollment.section_id:
        section = enrollment.section
        adviser = section.teacher

        classmates = (
            Student.objects.filter(
                enrollments__section_id=section.id,
                enrollments__school_year__is_active=True,
                enrollments__status__in=['Pending', 'Enrolled'],
            )
            .select_related('user')
            .distinct()
            .order_by('last_name', 'first_name')
        )

    return render(
        request,
        'accounts/student_people.html',
        {
            'student': student,
            'enrollment': enrollment,
            'section': section,
            'adviser': adviser,
            'classmates': classmates,
        },
    )



    try:
        student = request.user.student
    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found. Please contact administrator.')
        return redirect('home')

    if request.method == 'POST':
        form = ConcernForm(request.POST)
        if form.is_valid():
            concern = form.save(commit=False)
            concern.student = student
            concern.save()
            messages.success(request, 'Concern submitted successfully!')
            return redirect('student_concern')
    else:
        form = ConcernForm()
    concerns = Concern.objects.filter(student=student).order_by('-date_filed')
    return render(request, 'support/student_concern.html', {'form': form, 'concerns': concerns})




@login_required
@staff_required
def admin_portal_dashboard(request):
    total_students = Student.objects.count()
    enrolled = Enrollment.objects.filter(status='Enrolled', school_year__is_active=True).count()
    pending = Enrollment.objects.filter(status='Pending', school_year__is_active=True).count()
    total_tuition = Enrollment.objects.filter(school_year__is_active=True).aggregate(total=Count('id'))['total'] * 10000 # Default tuition
    active_enrollments = Enrollment.objects.filter(school_year__is_active=True)
    total_tuition_sum = sum(e.tuition_fee for e in active_enrollments)
    total_collected = sum(e.total_paid for e in active_enrollments)
    total_balance = sum(e.balance for e in active_enrollments)
    
    return render(
        request,
        'admin_dashboard.html',
        {
            'total_students': total_students,
            'enrolled': enrolled,
            'pending': pending,
            'by_grade': by_grade,
            'total_tuition': total_tuition_sum,
            'total_collected': total_collected,
            'total_balance': total_balance,
        },
    )


@login_required
@staff_required
def admin_portal_students(request):
    query = request.GET.get('q', '')
    students = Student.objects.select_related('user').filter(
        Q(user__first_name__icontains=query) | Q(user__last_name__icontains=query) | Q(student_id__icontains=query)
    )
    paginator = Paginator(students, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'accounts/admin_portal_students.html', {'page_obj': page_obj, 'query': query})


@login_required
@staff_required
def admin_delete_student(request, pk):
    """Admin can delete students. The signal in models.py handles User cleanup."""
    try:
        student = Student.objects.get(pk=pk)
        name = student.full_name
        student.delete()
        messages.success(request, f'Student {name} and their account have been deleted.')
    except Student.DoesNotExist:
        messages.error(request, 'Student not found.')
    
    return redirect('admin_portal_students')


@login_required
@staff_required
def admin_portal_enrollment(request):
    school_year = request.GET.get('school_year')
    grade = request.GET.get('grade')
    enrollments = Enrollment.objects.select_related('student__user', 'grade_level', 'section', 'school_year')
    if school_year:
        enrollments = enrollments.filter(school_year_id=school_year)
    if grade:
        enrollments = enrollments.filter(grade_level_id=grade)
    paginator = Paginator(enrollments, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'enrollment/admin_portal_enrollment.html', {'page_obj': page_obj})


@login_required
@staff_required
def admin_portal_sections(request):
    sections = Section.objects.select_related('grade_level', 'school_year')
    return render(request, 'academics/admin_portal_sections.html', {'sections': sections})


@login_required
@staff_required
def admin_portal_subjects(request):
    subjects = Subject.objects.select_related('grade_level')
    return render(request, 'academics/admin_portal_subjects.html', {'subjects': subjects})


@login_required
@staff_required
def admin_portal_schedule(request):
    schedules = ClassSchedule.objects.select_related('subject', 'section')
    return render(request, 'academics/admin_portal_schedule.html', {'schedules': schedules})




@login_required
@staff_required
def admin_portal_school_year(request):
    school_years = SchoolYear.objects.all()
    return render(request, 'academics/admin_portal_school_year.html', {'school_years': school_years})


@login_required
def about(request):
    template = 'about_admin.html' if request.user.is_staff else 'about.html'
    return render(request, template)


# ============================================================================
# ADMIN REGISTRATION VIEWS (Phase 2)
# ============================================================================

@login_required
@staff_required
def admin_register_teacher(request):
    """Admin can register teachers"""
    if request.method == 'POST':
        from apps.accounts.forms import TeacherRegistrationForm
        form = TeacherRegistrationForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            login_email = generate_email(data['first_name'], data['last_name'])
            
            try:
                with transaction.atomic():
                    user = User.objects.create_user(
                        username=login_email,
                        email=data['email'],
                        password=data['password'],
                        first_name=data['first_name'],
                        last_name=data['last_name'],
                        is_staff=True,
                    )
                    
                    teacher = Teacher.objects.create(
                        user=user,
                        first_name=data['first_name'],
                        last_name=data['last_name'],
                        middle_name=data.get('middle_name', ''),
                        birthdate=data['birthdate'],
                        gender=data['gender'],
                        address=data['address'],
                        contact_number=data['contact_number'],
                    )
            except IntegrityError:
                form.add_error('email', 'A user with this email already exists.')
            else:
                messages.success(request, f'Teacher {teacher.full_name} registered successfully!')
                return redirect('admin_portal_students')
    else:
        from apps.accounts.forms import TeacherRegistrationForm
        form = TeacherRegistrationForm()
    
    return render(request, 'accounts/admin_register_teacher.html', {'form': form})


@login_required
@staff_required
def admin_register_student(request):
    """Admin can register students"""
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            contact_email = data['email']
            login_email = generate_email(data['first_name'], data['last_name'])
            
            try:
                with transaction.atomic():
                    user = User.objects.create_user(
                        username=login_email,
                        email=contact_email,
                        password=data['password'],
                        first_name=data['first_name'],
                        last_name=data['last_name'],
                    )
                    student = Student.objects.create(
                        user=user,
                        first_name=data['first_name'],
                        last_name=data['last_name'],
                        middle_name=data['middle_name'],
                        birthdate=data['birthdate'],
                        gender=data['gender'],
                        address=data['address'],
                        contact_number=data['contact_number'],
                        guardian_name=data['guardian_name'],
                        guardian_contact=data['guardian_contact'],
                    )
            except IntegrityError:
                form.add_error('email', 'A user with this email already exists.')
            else:
                messages.success(request, f'Student {student.full_name} registered successfully!')
                return redirect('admin_portal_students')
    else:
        from apps.accounts.forms import StudentRegistrationForm
        form = StudentRegistrationForm()
    
    return render(request, 'accounts/admin_register_student.html', {'form': form})


# ============================================================================
# PROFESSOR VIEWS ENHANCEMENTS (Phase 2 & 3)
# ============================================================================

@login_required
@staff_required
def teacher_profile(request):
    """Teacher profile view"""
    try:
        teacher = request.user.teacher
    except Teacher.DoesNotExist:
        messages.error(request, 'Teacher profile not found.')
        return redirect('home')

    # Get current teaching assignments
    current_year = SchoolYear.objects.filter(is_active=True).first()
    teaching_assignments = ClassSchedule.objects.filter(
        teacher=teacher,
        school_year=current_year
    ).select_related('subject', 'section') if current_year else ClassSchedule.objects.none()

    return render(request, 'accounts/teacher_profile.html', {
        'teacher': teacher,
        'teaching_assignments': teaching_assignments,
        'active_page': 'profile',
    })



@login_required
@staff_required
def teacher_schedule(request):
    """Teacher view their schedule"""
    try:
        teacher = request.user.teacher
    except Teacher.DoesNotExist:
        messages.error(request, 'Teacher profile not found.')
        return redirect('home')

    current_year = SchoolYear.objects.filter(is_active=True).first()
    schedules = ClassSchedule.objects.filter(
        teacher=teacher,
        school_year=current_year
    ).select_related('subject', 'section').order_by('day', 'time_start') if current_year else ClassSchedule.objects.none()

    days = [('Mon', 'Monday'), ('Tue', 'Tuesday'), ('Wed', 'Wednesday'), 
            ('Thu', 'Thursday'), ('Fri', 'Friday'), ('Sat', 'Saturday')]
    time_slots = ['08:00', '09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00']

    return render(request, 'accounts/teacher_schedule.html', {
        'teacher': teacher,
        'schedules': schedules,
        'days': days,
        'time_slots': time_slots,
        'active_page': 'schedule',
    })


@login_required
@staff_required
def teacher_sections(request):
    try:
        teacher = request.user.teacher
    except Teacher.DoesNotExist:
        messages.error(request, 'Teacher profile not found.')
        return redirect('home')

    current_year = SchoolYear.objects.filter(is_active=True).first()
    
    sections = Section.objects.none()
    if current_year:
        from django.db.models import Q
        sections = Section.objects.filter(
            Q(schedules__teacher=teacher) | Q(teacher=teacher),
            school_year=current_year
        ).distinct()

        from apps.student.models import Enrollment
        for section in sections:
            section.subject_list = section.schedules.all()
            section.student_list = Enrollment.objects.filter(
                section=section, 
                status__in=['Pending', 'Enrolled', 'Paid']
            ).select_related('student')

    return render(request, 'accounts/teacher_sections.html', {
        'teacher': teacher,
        'sections': sections,
        'active_page': 'sections',
    })


@login_required
@staff_required
def teacher_adviser_setup(request):
    try:
        teacher = request.user.teacher
    except Teacher.DoesNotExist:
        messages.error(request, 'Teacher profile not found.')
        return redirect('home')

    from apps.student.forms import TeacherAdviserSubjectsForm

    if request.method == 'POST':
        form = TeacherAdviserSubjectsForm(request.POST, teacher=teacher)
        if form.is_valid():
            adviser_section = form.cleaned_data['adviser_section']
            subjects = form.cleaned_data['subjects']

            # Enforce 1 adviser section per teacher: clear any previous assignments
            Section.objects.filter(teacher=teacher).exclude(pk=adviser_section.pk).update(teacher=None)

            # Assign teacher as adviser for the chosen section
            if adviser_section.teacher_id != teacher.id:
                adviser_section.teacher = teacher
                adviser_section.save(update_fields=['teacher'])

            # Save teacher subject skills
            teacher.subjects.set(subjects)

            messages.success(request, 'Adviser section and subjects saved successfully!')
            return redirect('teacher_dashboard')
    else:
        form = TeacherAdviserSubjectsForm(teacher=teacher)

    current_adviser_section = Section.objects.filter(teacher=teacher).select_related('grade_level', 'school_year').first()

    return render(request, 'accounts/teacher_adviser_setup.html', {
        'teacher': teacher,
        'form': form,
        'current_adviser_section': current_adviser_section,
        'active_page': 'sections',
    })


@login_required
@staff_required
def teacher_ai_assistance(request):
    try:
        teacher = request.user.teacher
    except Teacher.DoesNotExist:
        messages.error(request, 'Teacher profile not found.')
        return redirect('home')

    question = ''
    ai_response = None
    if request.method == 'POST':
        question = request.POST.get('question', '').strip()
        if question:
            ai_response = (
                'This page is a teaching assistant placeholder. For live AI integration, connect your assistant service in the portal settings.'
            )
    return render(request, 'accounts/teacher_ai_assistance.html', {
        'teacher': teacher,
        'question': question,
        'ai_response': ai_response,
        'active_page': 'ai',
    })


# ============================================================================
# SCHOOL DATA MANAGEMENT VIEWS (Phase 3)
# ============================================================================






