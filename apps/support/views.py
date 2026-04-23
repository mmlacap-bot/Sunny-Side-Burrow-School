from django.db import models
from django.db.models import Q, OuterRef, Subquery, Value
from django.db.models.functions import Coalesce
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import redirect, render, get_object_or_404
from django.utils import timezone
from django.http import JsonResponse

from apps.academics.models import ClassSchedule, SchoolYear, Section
from apps.student.models import Concern, Enrollment, Teacher, Student
from .models import DirectThread, DirectMessage, MessageStatus

staff_required = user_passes_test(lambda u: u.is_staff)


@login_required
def student_concern(request):
    try:
        student = request.user.student
    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found. Please contact administrator.')
        return redirect('home')

    if request.method == 'POST':
        from .forms import ConcernForm
        form = ConcernForm(request.POST)
        if form.is_valid():
            concern = form.save(commit=False)
            concern.student = student
            concern.save()
            messages.success(request, 'Concern submitted successfully!')
            return redirect('student_concern')
    else:
        from .forms import ConcernForm
        form = ConcernForm()
    concerns = Concern.objects.filter(student=student).order_by('-date_filed')
    return render(request, 'support/student_concern.html', {'form': form, 'concerns': concerns})


@login_required
@staff_required
def admin_portal_concerns(request):
    concerns = Concern.objects.select_related('student__user')
    return render(request, 'support/admin_portal_concerns.html', {'concerns': concerns})


@login_required
@staff_required
def teacher_concerns(request):
    """Teacher view for responding to concerns"""
    try:
        teacher = request.user.teacher
    except Teacher.DoesNotExist:
        messages.error(request, 'Teacher profile not found.')
        return redirect('home')

    # Get all concerns for subjects taught by this teacher
    current_year = SchoolYear.objects.filter(is_active=True).first()
    
    # Include both advisory sections and sections taught by schedule assignment
    taught_sections = Section.objects.filter(schedules__teacher=teacher, schedules__school_year=current_year)
    advisory_sections = Section.objects.filter(teacher=teacher, school_year=current_year)
    sections = (taught_sections | advisory_sections).distinct()
    enrollments = Enrollment.objects.filter(section__in=sections, school_year=current_year, status__in=['Pending', 'Enrolled'])
    students = Student.objects.filter(enrollments__in=enrollments).distinct()

    concerns = Concern.objects.filter(student__in=students).select_related('student__user').order_by('-date_filed')

    return render(request, 'support/teacher_concerns.html', {
        'teacher': teacher,
        'concerns': concerns,
        'active_page': 'concerns',
    })


@login_required
@staff_required
def teacher_respond_concern(request, concern_id):
    """Teacher respond to a concern"""
    try:
        concern = Concern.objects.get(pk=concern_id)
    except Concern.DoesNotExist:
        messages.error(request, 'Concern not found.')
        return redirect('teacher_concerns')

    if request.method == 'POST':
        from .forms import ConcernResponseForm
        form = ConcernResponseForm(request.POST, instance=concern)
        if form.is_valid():
            response = form.cleaned_data['response']
            try:
                concern = form.save(commit=False)
                concern.add_response(request.user, response)
                messages.success(request, 'Response added successfully!')
                return redirect('teacher_concerns')
            except Exception as e:
                messages.error(request, f'Error: {str(e)}')
    else:
        from .forms import ConcernResponseForm
        form = ConcernResponseForm(instance=concern)

    return render(request, 'support/teacher_respond_concern.html', {
        'form': form,
        'concern': concern,
    })


@login_required
@staff_required
def admin_respond_concern(request, concern_id):
    """Admin respond to a concern"""
    try:
        concern = Concern.objects.get(pk=concern_id)
    except Concern.DoesNotExist:
        messages.error(request, 'Concern not found.')
        return redirect('admin_portal_concerns')

    if request.method == 'POST':
        from .forms import ConcernResponseForm
        form = ConcernResponseForm(request.POST, instance=concern)
        if form.is_valid():
            concern = form.save(commit=False)
            concern.add_response(request.user, form.cleaned_data['response'])
            messages.success(request, 'Response added successfully!')
            return redirect('admin_portal_concerns')
    else:
        from .forms import ConcernResponseForm
        form = ConcernResponseForm(instance=concern)

    return render(request, 'support/admin_respond_concern.html', {
        'form': form,
        'concern': concern,
    })


@login_required
@staff_required
def admin_resolve_concern(request, concern_id):
    """Admin resolve a concern"""
    try:
        concern = Concern.objects.get(pk=concern_id)
    except Concern.DoesNotExist:
        messages.error(request, 'Concern not found.')
        return redirect('admin_portal_concerns')

    if request.method == 'POST':
        from .forms import ResolveConcernForm
        form = ResolveConcernForm(request.POST)
        if form.is_valid():
            try:
                concern.resolve_concern(request.user, form.cleaned_data.get('response', ''))
                messages.success(request, 'Concern resolved successfully!')
                return redirect('admin_portal_concerns')
            except Exception as e:
                messages.error(request, f'Error: {str(e)}')
    else:
        from .forms import ResolveConcernForm
        form = ResolveConcernForm()


from apps.academics.models import TeacherApplication, ClassSchedule, Section, SchoolYear

# ============================================================================
# INBOX MESSAGING (Direct Messaging)
# ============================================================================

def _student_allowed_recipient_ids(student: Student) -> set[int]:
    """
    Returns a set of User IDs that a student is allowed to message.
    Students can message all teachers by default.
    """
    all_teacher_user_ids = set(Teacher.objects.values_list('user_id', flat=True))
    
    # Also include classmates in the same section if enrolled
    classmate_user_ids = set()
    current_year = SchoolYear.objects.filter(is_active=True).first()
    if current_year:
        enrollment = Enrollment.objects.filter(student=student, school_year=current_year).first()
        if enrollment and enrollment.section:
            classmate_user_ids = set(
                Enrollment.objects.filter(section=enrollment.section, school_year=current_year)
                .exclude(student=student)
                .values_list('student__user_id', flat=True)
            )
            
    return all_teacher_user_ids | classmate_user_ids


@login_required
def student_inbox(request, thread_id=None):
    try:
        student = request.user.student
    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found.')
        return redirect('home')

    # Subquery for last message body and timestamp
    last_body_sub = Subquery(
        DirectMessage.objects.filter(thread=OuterRef('pk'))
        .order_by('-created_at')
        .values('body')[:1],
        output_field=models.TextField()
    )
    last_at_sub = Subquery(
        DirectMessage.objects.filter(thread=OuterRef('pk'))
        .order_by('-created_at')
        .values('created_at')[:1]
    )

    threads = (
        DirectThread.objects.filter(Q(user1=request.user) | Q(user2=request.user))
        .select_related('user1', 'user2')
        .annotate(last_message_body=Coalesce(last_body_sub, Value('', output_field=models.TextField())))
        .annotate(last_message_at=last_at_sub)
        .order_by('-updated_at')
    )

    # Process each thread for display name/unread count
    for t in threads:
        other_user = t.user2 if t.user1 == request.user else t.user1
        t.other_user = other_user
        t.unread_count = t.messages.filter(receiver=request.user, status=MessageStatus.SENT).count()

    active_thread = None
    messages_list = []
    if thread_id:
        active_thread = get_object_or_404(DirectThread, pk=thread_id)
        # Security check
        if active_thread.user1 != request.user and active_thread.user2 != request.user:
            messages.error(request, "Access denied.")
            return redirect('student_inbox')
        
        # Mark messages as READ
        active_thread.messages.filter(receiver=request.user, status=MessageStatus.SENT).update(
            status=MessageStatus.READ, 
            read_at=timezone.now()
        )
        
        messages_list = active_thread.messages.all().order_by('created_at')
        active_thread.other_user = active_thread.user2 if active_thread.user1 == request.user else active_thread.user1

    # Handle sending a new message
    if request.method == 'POST' and active_thread:
        body = request.POST.get('body', '').strip()
        if body:
            receiver = active_thread.other_user
            DirectMessage.objects.create(
                thread=active_thread,
                sender=request.user,
                receiver=receiver,
                body=body
            )
            active_thread.updated_at = timezone.now()
            active_thread.save()
            return redirect('student_inbox_detail', thread_id=active_thread.pk)

    allowed_ids = _student_allowed_recipient_ids(student)
    contacts = []
    # Fetch teachers
    teachers = Teacher.objects.all().select_related('user')
    for t in teachers:
        contacts.append({'id': t.user.id, 'name': f"{t.full_name} (Teacher)", 'is_teacher': True})
    
    # Fetch classmates if section exists
    current_year = SchoolYear.objects.filter(is_active=True).first()
    if current_year:
        enrollment = Enrollment.objects.filter(student=student, school_year=current_year).first()
        if enrollment and enrollment.section:
            classmates = Enrollment.objects.filter(section=enrollment.section, school_year=current_year).exclude(student=student).select_related('student__user')
            for c in classmates:
                contacts.append({'id': c.student.user.id, 'name': f"{c.student.full_name} (Classmate)", 'is_teacher': False})

    return render(request, 'support/student_inbox.html', {
        'threads': threads,
        'active_thread': active_thread,
        'messages_list': messages_list,
        'contacts': contacts,
        'active_page': 'inbox'
    })


@login_required
@staff_required
def teacher_inbox(request, thread_id=None):
    try:
        teacher = request.user.teacher
    except Teacher.DoesNotExist:
        messages.error(request, 'Teacher profile not found.')
        return redirect('home')

    last_body_sub = Subquery(
        DirectMessage.objects.filter(thread=OuterRef('pk'))
        .order_by('-created_at')
        .values('body')[:1],
        output_field=models.TextField()
    )
    last_at_sub = Subquery(
        DirectMessage.objects.filter(thread=OuterRef('pk'))
        .order_by('-created_at')
        .values('created_at')[:1]
    )

    threads = (
        DirectThread.objects.filter(Q(user1=request.user) | Q(user2=request.user))
        .select_related('user1', 'user2')
        .annotate(last_message_body=Coalesce(last_body_sub, Value('', output_field=models.TextField())))
        .annotate(last_message_at=last_at_sub)
        .order_by('-updated_at')
    )

    for t in threads:
        other_user = t.user2 if t.user1 == request.user else t.user1
        t.other_user = other_user
        t.unread_count = t.messages.filter(receiver=request.user, status=MessageStatus.SENT).count()

    active_thread = None
    messages_list = []
    if thread_id:
        active_thread = get_object_or_404(DirectThread, pk=thread_id)
        if active_thread.user1 != request.user and active_thread.user2 != request.user:
            messages.error(request, "Access denied.")
            return redirect('teacher_inbox')
        
        active_thread.messages.filter(receiver=request.user, status=MessageStatus.SENT).update(
            status=MessageStatus.READ, 
            read_at=timezone.now()
        )
        messages_list = active_thread.messages.all().order_by('created_at')
        active_thread.other_user = active_thread.user2 if active_thread.user1 == request.user else active_thread.user1

    if request.method == 'POST' and active_thread:
        body = request.POST.get('body', '').strip()
        if body:
            DirectMessage.objects.create(
                thread=active_thread,
                sender=request.user,
                receiver=active_thread.other_user,
                body=body
            )
            active_thread.updated_at = timezone.now()
            active_thread.save()
            return redirect('teacher_inbox_detail', thread_id=active_thread.pk)

    # For teachers, contacts are all students they teach + fellow teachers
    contacts = []
    students = Student.objects.all().select_related('user')
    for s in students:
        contacts.append({'id': s.user.id, 'name': f"{s.full_name} (Student)", 'is_teacher': False})
    
    teachers = Teacher.objects.exclude(user=request.user).select_related('user')
    for t in teachers:
        contacts.append({'id': t.user.id, 'name': f"{t.full_name} (Teacher)", 'is_teacher': True})

    return render(request, 'support/teacher_inbox.html', {
        'threads': threads,
        'active_thread': active_thread,
        'messages_list': messages_list,
        'contacts': contacts,
        'active_page': 'inbox'
    })


@login_required
def start_conversation(request):
    """AJAX view to start or get an existing thread between two users."""
    user_id = request.GET.get('user_id')
    if not user_id:
        return JsonResponse({'error': 'User ID required'}, status=400)
    
    from django.contrib.auth import get_user_model
    User = get_user_model()
    target_user = get_object_or_404(User, pk=user_id)
    
    if target_user == request.user:
        return JsonResponse({'error': 'Cannot message yourself'}, status=400)
    
    # Enforce standard order for user1/user2 to maintain uniqueness
    u1, u2 = sorted([request.user.id, target_user.id])
    thread, created = DirectThread.objects.get_or_create(
        user1_id=u1,
        user2_id=u2
    )
    
    if hasattr(request.user, 'teacher'):
        url = f"/teacher_inbox/{thread.id}/"
    else:
        url = f"/student_inbox/{thread.id}/"
        
    return JsonResponse({'url': url})


@login_required
def search_users(request):
    """Simple AJAX search for contacts."""
    q = request.GET.get('q', '').strip()
    if len(q) < 2:
        return JsonResponse({'results': []})
    
    results = []
    # Search Teachers
    teachers = Teacher.objects.filter(
        Q(first_name__icontains=q) | Q(last_name__icontains=q)
    ).select_related('user')[:5]
    for t in teachers:
        results.append({'id': t.user.id, 'name': f"{t.full_name} (Teacher)"})
        
    # Search Students
    students = Student.objects.filter(
        Q(first_name__icontains=q) | Q(last_name__icontains=q)
    ).select_related('user')[:5]
    for s in students:
        results.append({'id': s.user.id, 'name': f"{s.full_name} (Student)"})
        
    return JsonResponse({'results': results})

@login_required
def teacher_applications(request):
    """View for teachers to apply for subjects and advisory sections (restored to Wednesday version)"""
    try:
        teacher = request.user.teacher
    except Teacher.DoesNotExist:
        messages.error(request, 'Teacher profile not found.')
        return redirect('home')

    active_year = SchoolYear.objects.filter(is_active=True).first()
    if not active_year:
        messages.error(request, 'No active school year configured.')
        return redirect('teacher_dashboard')

    # Check specific assignments
    has_subject_assignment = TeacherApplication.objects.filter(
        teacher=teacher, 
        school_year=active_year, 
        application_type='SUBJECT',
        status='APPROVED'
    ).exists()
    
    has_advisory_assignment = TeacherApplication.objects.filter(
        teacher=teacher, 
        school_year=active_year, 
        application_type='ADVISORY',
        status='APPROVED'
    ).exists()

    from apps.academics.forms import TeacherApplicationForm
    if request.method == 'POST':
        app_type = request.POST.get('application_type')
        
        if app_type == 'SUBJECT' and has_subject_assignment:
            messages.error(request, 'You already have a subject assignment.')
            return redirect('teacher_applications')
        if app_type == 'ADVISORY' and has_advisory_assignment:
            messages.error(request, 'You already have an advisory assignment.')
            return redirect('teacher_applications')

        form = TeacherApplicationForm(request.POST, school_year=active_year)
        if form.is_valid():
            notes = form.cleaned_data['notes']
            
            from django.db import transaction
            if app_type == 'SUBJECT':
                schedules = form.cleaned_data['class_schedules']
                if len(schedules) != 8:
                    messages.error(request, 'You must select exactly 8 subjects to apply.')
                    return redirect('teacher_applications')

                # Check for time conflicts
                has_conflicts = False
                for i in range(len(schedules)):
                    for j in range(i + 1, len(schedules)):
                        s1 = schedules[i]
                        s2 = schedules[j]
                        if s1.day == s2.day or s1.day == 'Dly' or s2.day == 'Dly':
                            if s1.time_start < s2.time_end and s2.time_start < s1.time_end:
                                has_conflicts = True
                                break
                    if has_conflicts:
                        break
                        
                if has_conflicts:
                    messages.error(request, 'You have selected subjects with conflicting schedules.')
                    return redirect('teacher_applications')

                created_count = 0
                try:
                    with transaction.atomic():
                        for schedule in schedules:
                            locked_schedule = ClassSchedule.objects.select_for_update().get(pk=schedule.pk)
                            if not locked_schedule.teacher:
                                TeacherApplication.objects.create(
                                    teacher=teacher,
                                    school_year=active_year,
                                    application_type='SUBJECT',
                                    class_schedule=locked_schedule,
                                    notes=notes,
                                    status='APPROVED',
                                    reviewed_at=timezone.now(),
                                    review_notes='Automatically approved by system.'
                                )
                                locked_schedule.teacher = teacher
                                locked_schedule.save(update_fields=['teacher'])
                                created_count += 1
                except Exception as e:
                    messages.error(request, f'Error during subject assignment: {str(e)}')
                    return redirect('teacher_applications')
                
                if created_count > 0:
                    messages.success(request, f'Successfully assigned to {created_count} subject(s).')
                else:
                    messages.warning(request, 'No subjects were assigned (taken by another teacher).')
                return redirect('teacher_applications')
            else:
                section = form.cleaned_data['section']
                if not section:
                    messages.error(request, 'Please select an advisory section.')
                    return redirect('teacher_applications')

                try:
                    with transaction.atomic():
                        locked_section = Section.objects.select_for_update().get(pk=section.pk)
                        if locked_section.teacher:
                            messages.error(request, f'Section {locked_section} already has an advisor.')
                        else:
                            TeacherApplication.objects.create(
                                teacher=teacher,
                                school_year=active_year,
                                application_type='ADVISORY',
                                section=locked_section,
                                notes=notes,
                                status='APPROVED',
                                reviewed_at=timezone.now(),
                                review_notes='Automatically approved by system.'
                            )
                            locked_section.teacher = teacher
                            locked_section.save(update_fields=['teacher'])
                            messages.success(request, f'You are now the Advisory Teacher for {locked_section}.')
                except Exception as e:
                    messages.error(request, f'Error assigning advisor: {str(e)}')
                return redirect('teacher_applications')
    else:
        form = TeacherApplicationForm(school_year=active_year)

    applications = TeacherApplication.objects.filter(
        teacher=teacher,
        school_year=active_year
    ).order_by('-created_at')

    # For frontend JS exclusivity check
    occupied_sections_ids = list(Section.objects.filter(
        school_year=active_year
    ).filter(
        models.Q(teacher__isnull=False) | 
        models.Q(teacher_applications__status__in=['PENDING', 'APPROVED'], teacher_applications__application_type='ADVISORY')
    ).values_list('id', flat=True).distinct())

    return render(request, 'support/teacher_applications.html', {
        'form': form,
        'applications': applications,
        'occupied_sections_ids': occupied_sections_ids,
        'has_subject_assignment': has_subject_assignment,
        'has_advisory_assignment': has_advisory_assignment,
        'active_page': 'applications',
    })
