import datetime
import random

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.shortcuts import redirect, render

from apps.academics.models import ClassSchedule, GradeLevel, SchoolYear, Section, Subject
from apps.student.models import Enrollment, EnrollmentSubject, Student

staff_required = user_passes_test(lambda u: u.is_staff)


def normalize_for_email(value):
    return ''.join(ch.lower() for ch in value if ch.isalnum())


def generate_email(first_name, last_name):
    base_first = normalize_for_email(first_name) or 'user'
    base_last = normalize_for_email(last_name)
    local_part = f"{base_first}.{base_last}" if base_last else base_first
    for _ in range(20):
        login_email = f"{local_part}{random.randint(100, 999)}@sunnyday.edu.ph"
        if not Student.objects.filter(user__username__iexact=login_email).exists():
            return login_email
    suffix = 1
    while True:
        login_email = f"{local_part}{suffix:03d}@sunnyday.edu.ph"
        if not Student.objects.filter(user__username__iexact=login_email).exists():
            return login_email
        suffix += 1


def ensure_enrollment_reference_data():
    """
    Optimized reference data check.
    Only runs heavy logic if essential data is missing.
    """
    active_year = SchoolYear.objects.filter(is_active=True).first()
    
    # Fast check: If we have an active year and basic structures exist, skip seeding.
    if active_year:
        has_grades = GradeLevel.objects.exists()
        has_sections = Section.objects.filter(school_year=active_year).exists()
        if has_grades and has_sections:
            return active_year

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

    # Remove legacy combined or redundant grade levels if they still exist.
    for old_name in ['Kindergarten', 'Kinder & Preparatory', 'Grade 4-6', 'Grade 1-2']:
        for old_grade in GradeLevel.objects.filter(name=old_name):
            Section.objects.filter(grade_level=old_grade).delete()
            Subject.objects.filter(grade_level=old_grade).delete()
            Enrollment.objects.filter(grade_level=old_grade).update(grade_level=grade_levels.get('Grade 1', old_grade))
            old_grade.delete()

    # Purge legacy subjects - MOVED to conditional to avoid re-scanning
    # Only run if no subjects exist yet for the grade levels
    if not Subject.objects.exists():
        import re
        numeric_pattern = re.compile(r'^\d+$')
        for subj in Subject.objects.all():
            if not numeric_pattern.match(subj.code):
                subj.delete()

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
        
        recess = subjects.filter(name='Recess').first()
        other_subjects = list(subjects.exclude(name='Recess'))
        
        # Room Calculation: Grade Order -> Letter (1=A, 2=B, etc.)
        # Section Name -> Number (A=001, B=002)
        base_letter = chr(64 + grade_level.level_order)
        room_num = "001" if section.name == "A" else "002"
        main_room = f"{base_letter}{room_num}"

        if recess:
            ClassSchedule.objects.update_or_create(
                subject=recess,
                section=section,
                school_year=active_year,
                defaults={
                    'day': 'Dly',
                    'time_start': datetime.time(10, 0),
                    'time_end': datetime.time(10, 30),
                    'room': 'School Canteen',
                    'teacher': None,
                },
            )
            
        mwf_hour = 8
        tth_hour = 8
        for idx, subject in enumerate(other_subjects):
            if idx % 2 == 0:
                day = 'MWF'
                start_hour = mwf_hour
                if start_hour == 10: start_hour = 11
                end_hour = start_hour + 1
                mwf_hour = end_hour
            else:
                day = 'TTH'
                start_hour = tth_hour
                if start_hour == 10: start_hour = 11
                end_hour = start_hour + 1
                tth_hour = end_hour
                
            ClassSchedule.objects.update_or_create(
                subject=subject,
                section=section,
                school_year=active_year,
                defaults={
                    'day': day,
                    'time_start': datetime.time(start_hour, 0),
                    'time_end': datetime.time(end_hour, 0),
                    'room': main_room,
                    'teacher': None,
                },
            )


@login_required
def student_enrollment(request):
    try:
        student = request.user.student
    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found. Please contact administrator.')
        return redirect('home')

    # Check for existing enrollment first to return fast
    enrollment = Enrollment.objects.filter(student=student, school_year__is_active=True).first()
    if enrollment:
        enrolled_subjects = EnrollmentSubject.objects.filter(enrollment=enrollment).select_related('class_schedule__subject')
        return render(
            request,
            'enrollment/student_enrollment.html',
            {
                'student': student,
                'enrollment': enrollment,
                'enrolled_subjects': enrolled_subjects,
            },
        )

    # Only ensure reference data if the student is not yet enrolled and about to start/continue the process
    ensure_enrollment_reference_data()

    if request.method == 'POST':
        step = request.POST.get('step', '1')
        if step == '1':
            from apps.accounts.forms import StudentProfileForm
            profile_form = StudentProfileForm(request.POST, instance=student)
            if profile_form.is_valid():
                profile_form.save()
                from .forms import EnrollmentForm
                form = EnrollmentForm(student=student)
                return render(request, 'enrollment/student_enrollment.html', {'step': 2, 'student': student, 'form': form})
            return render(request, 'enrollment/student_enrollment.html', {'step': 1, 'student': student, 'profile_form': profile_form})

        if step == '2':
            from .forms import EnrollmentForm
            form = EnrollmentForm(request.POST, student=student)
            action = request.POST.get('action', 'confirm')
            section = None
            grade_level = None
            subject_rows = []

            if form.is_bound and request.POST.get('grade_level') and request.POST.get('section'):
                grade_level = form.fields['grade_level'].queryset.filter(id=request.POST.get('grade_level')).first()
                section = form.fields['section'].queryset.filter(id=request.POST.get('section')).first()
                school_year = form.fields['school_year'].queryset.filter(id=request.POST.get('school_year')).first()
                if grade_level and section and school_year:
                    subjects = Subject.objects.filter(grade_level=grade_level).order_by('code', 'name')
                    schedules = {
                        schedule.subject_id: schedule
                        for schedule in ClassSchedule.objects.filter(
                            subject__in=subjects,
                            section=section,
                            school_year=school_year,
                        ).select_related('subject')
                    }
                    day_priority = {'Mon': 1, 'Tue': 2, 'Wed': 3, 'Thu': 4, 'Fri': 5, 'Sat': 6, 'MWF': 7, 'TTH': 8, 'Dly': 9}
                    for subject in subjects:
                        schedule = schedules.get(subject.id)
                        subject_rows.append(
                            {
                                'subject': subject,
                                'section': section,
                                'day': schedule.day if schedule else 'N/A',
                                'time': (
                                    f'{schedule.time_start.strftime("%H:%M")} - {schedule.time_end.strftime("%H:%M")}'
                                    if schedule
                                    else 'N/A'
                                ),
                                'room': schedule.room if schedule else 'N/A',
                                'availability': 'Okay to Enroll' if schedule else 'Closed',
                                'day_priority': day_priority.get(schedule.day, 99) if schedule else 99,
                                'time_start_val': schedule.time_start if schedule else datetime.time(23, 59),
                            }
                        )
                    
                    # Sort the rows order by day priority and time
                    subject_rows.sort(key=lambda x: (x['day_priority'], x['time_start_val']))

            if action == 'confirm' and form.is_valid():
                school_year = form.cleaned_data['school_year']
                grade_level = form.cleaned_data['grade_level']
                selected_section = form.cleaned_data['section']

                try:
                    with transaction.atomic():
                        locked_section = Section.objects.select_for_update().get(pk=selected_section.pk)
                        current_count = Enrollment.objects.select_for_update().filter(
                            section=locked_section,
                            school_year=school_year,
                            status__in=['Pending', 'Enrolled'],
                        ).count()

                        if current_count >= locked_section.max_students:
                            form.add_error('section', 'This section is already full.')
                            raise ValueError('Section is full')

                        subjects = list(Subject.objects.filter(grade_level=grade_level).order_by('code', 'name'))
                        schedules = list(
                            ClassSchedule.objects.filter(
                                subject__in=subjects,
                                section=locked_section,
                                school_year=school_year,
                            ).select_related('subject')
                        )
                        schedule_by_subject_id = {schedule.subject_id: schedule for schedule in schedules}
                        missing_subjects = [subject.name for subject in subjects if subject.id not in schedule_by_subject_id]
                        if missing_subjects:
                            form.add_error(
                                None,
                                'Unable to complete enrollment because some subjects do not have schedules: '
                                + ', '.join(missing_subjects),
                            )
                            raise ValueError('Missing schedules')

                        enrollment = Enrollment.objects.create(
                            student=student,
                            school_year=school_year,
                            grade_level=grade_level,
                            section=locked_section,
                            status='Pending',
                            enrolled_by=request.user,
                            tuition_fee=10000,
                        )
                        EnrollmentSubject.objects.bulk_create(
                            [
                                EnrollmentSubject(enrollment=enrollment, class_schedule=schedule)
                                for schedule in schedules
                            ]
                        )
                except IntegrityError:
                    form.add_error(None, 'You already have an enrollment record for the selected school year.')
                except ValueError:
                    pass
                else:
                    messages.success(request, 'Enrollment submitted successfully!')
                    return redirect('student_dashboard')

            return render(
                request,
                'enrollment/student_enrollment.html',
                {
                    'step': 2,
                    'student': student,
                    'form': form,
                    'section': section,
                    'grade_level': grade_level,
                    'subject_rows': subject_rows,
                },
            )

    from apps.accounts.forms import StudentProfileForm
    profile_form = StudentProfileForm(instance=student)
    return render(request, 'enrollment/student_enrollment.html', {'step': 1, 'student': student, 'profile_form': profile_form})


@login_required
def get_sections_by_grade_level(request):
    grade_level_id = request.GET.get('grade_level_id')
    school_year_id = request.GET.get('school_year_id')

    if not grade_level_id or not school_year_id:
        return JsonResponse({'error': 'Missing parameters'}, status=400)

    sections = Section.objects.filter(
        grade_level_id=grade_level_id,
        school_year_id=school_year_id,
    ).values('id', 'name').order_by('name')

    return JsonResponse(list(sections), safe=False)


@login_required
def get_schedule_by_section(request):
    section_id = request.GET.get('section_id')

    if not section_id:
        return JsonResponse({'error': 'Missing section_id'}, status=400)

    try:
        section = Section.objects.get(id=section_id)
    except Section.DoesNotExist:
        return JsonResponse({'error': 'Section not found'}, status=404)

    schedules = ClassSchedule.objects.filter(section=section).select_related('subject').values(
        'id',
        'subject__name',
        'day',
        'time_start',
        'time_end',
        'room',
    ).order_by('day', 'time_start')

    return JsonResponse(list(schedules), safe=False)


@login_required
@staff_required
def admin_create_enrollment(request):
    """Admin create enrollment for a student"""
    if request.method == 'POST':
        from .forms import EnrollmentForm
        student_id = request.POST.get('student_id')
        try:
            student = Student.objects.get(pk=student_id)
        except Student.DoesNotExist:
            messages.error(request, 'Student not found.')
            return redirect('admin_portal_enrollment')

        form = EnrollmentForm(request.POST, student=student)
        if form.is_valid():
            enrollment = form.save(commit=False)
            enrollment.student = student
            enrollment.enrolled_by = request.user
            enrollment.status = 'Enrolled'

            try:
                with transaction.atomic():
                    enrollment.save()
                    # Auto-create enrollment subjects
                    subjects = Subject.objects.filter(grade_level=enrollment.grade_level)
                    schedules = ClassSchedule.objects.filter(
                        subject__in=subjects,
                        section=enrollment.section,
                        school_year=enrollment.school_year,
                    )
                    EnrollmentSubject.objects.bulk_create([
                        EnrollmentSubject(enrollment=enrollment, class_schedule=schedule)
                        for schedule in schedules
                    ])
                messages.success(request, 'Enrollment created successfully!')
                return redirect('admin_portal_enrollment')
            except Exception as e:
                messages.error(request, f'Error: {str(e)}')
    else:
        from .forms import EnrollmentForm
        form = EnrollmentForm()

    students = Student.objects.all()
    return render(request, 'enrollment/admin_create_enrollment.html', {
        'form': form,
        'students': students,
    })


@login_required
@staff_required
def admin_update_enrollment(request, enrollment_id):
    """Admin update enrollment status"""
    try:
        enrollment = Enrollment.objects.get(pk=enrollment_id)
    except Enrollment.DoesNotExist:
        messages.error(request, 'Enrollment not found.')
        return redirect('admin_portal_enrollment')

    if request.method == 'POST':
        status = request.POST.get('status')
        if status in dict(Enrollment.STATUS_CHOICES):
            enrollment.status = status
            enrollment.save()
            messages.success(request, 'Enrollment status updated!')
            return redirect('admin_portal_enrollment')

    return render(request, 'enrollment/admin_update_enrollment.html', {
        'enrollment': enrollment,
        'status_choices': dict(Enrollment.STATUS_CHOICES),
    })


@login_required
def cancel_enrollment(request, enrollment_id):
    """Allow a student to cancel (delete) their pending enrollment"""
    try:
        enrollment = Enrollment.objects.get(pk=enrollment_id)
        
        # Ensure the enrollment belongs to the current user's student profile
        if enrollment.student.user != request.user:
            messages.error(request, "Permission denied.")
            return redirect('student_dashboard')
            
        # Only allow cancellation if status is 'Pending'
        if enrollment.status != 'Pending':
            messages.error(request, "Only pending enrollments can be cancelled. Please contact the registrar for other statuses.")
            return redirect('student_enrollment')
            
        with transaction.atomic():
            enrollment.delete()
            
        messages.success(request, "Your enrollment has been successfully cancelled.")
        return redirect('student_dashboard')
        
    except Enrollment.DoesNotExist:
        messages.error(request, "Enrollment record not found.")
        return redirect('student_dashboard')
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return redirect('student_dashboard')
