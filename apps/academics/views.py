from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import redirect, render

from .models import ClassSchedule, GradeLevel, SchoolYear, Section, Subject

staff_required = user_passes_test(lambda u: u.is_staff)


@login_required
@staff_required
def admin_manage_school_year(request, year_id=None):
    """Create or edit school year"""
    if year_id:
        try:
            school_year = SchoolYear.objects.get(pk=year_id)
        except SchoolYear.DoesNotExist:
            messages.error(request, 'School year not found.')
            return redirect('admin_portal_school_year')
    else:
        school_year = None

    if request.method == 'POST':
        from .forms import SchoolYearForm
        form = SchoolYearForm(request.POST, instance=school_year)
        if form.is_valid():
            form.save()
            messages.success(request, 'School year saved successfully!')
            return redirect('admin_portal_school_year')
    else:
        from .forms import SchoolYearForm
        form = SchoolYearForm(instance=school_year)

    return render(request, 'academics/admin_manage_school_year.html', {
        'form': form,
        'school_year': school_year,
    })


@login_required
@staff_required
def admin_manage_grade_level(request, grade_id=None):
    """Create or edit grade level"""
    if grade_id:
        try:
            grade_level = GradeLevel.objects.get(pk=grade_id)
        except GradeLevel.DoesNotExist:
            messages.error(request, 'Grade level not found.')
            return redirect('admin_portal_dashboard')
    else:
        grade_level = None

    if request.method == 'POST':
        from .forms import GradeLevelForm
        form = GradeLevelForm(request.POST, instance=grade_level)
        if form.is_valid():
            form.save()
            messages.success(request, 'Grade level saved successfully!')
            return redirect('admin_portal_dashboard')
    else:
        from .forms import GradeLevelForm
        form = GradeLevelForm(instance=grade_level)

    return render(request, 'academics/admin_manage_grade_level.html', {
        'form': form,
        'grade_level': grade_level,
    })


@login_required
@staff_required
def admin_manage_section(request, section_id=None):
    """Create or edit section"""
    if section_id:
        try:
            section = Section.objects.get(pk=section_id)
        except Section.DoesNotExist:
            messages.error(request, 'Section not found.')
            return redirect('admin_portal_sections')
    else:
        section = None

    if request.method == 'POST':
        from .forms import SectionForm
        form = SectionForm(request.POST, instance=section)
        if form.is_valid():
            form.save()
            messages.success(request, 'Section saved successfully!')
            return redirect('admin_portal_sections')
    else:
        from .forms import SectionForm
        form = SectionForm(instance=section)

    return render(request, 'academics/admin_manage_section.html', {
        'form': form,
        'section': section,
    })


@login_required
@staff_required
def admin_manage_subject(request, subject_id=None):
    """Create or edit subject"""
    if subject_id:
        try:
            subject = Subject.objects.get(pk=subject_id)
        except Subject.DoesNotExist:
            messages.error(request, 'Subject not found.')
            return redirect('admin_portal_subjects')
    else:
        subject = None

    if request.method == 'POST':
        from .forms import SubjectForm
        form = SubjectForm(request.POST, instance=subject)
        if form.is_valid():
            form.save()
            messages.success(request, 'Subject saved successfully!')
            return redirect('admin_portal_subjects')
    else:
        from .forms import SubjectForm
        form = SubjectForm(instance=subject)

    return render(request, 'academics/admin_manage_subject.html', {
        'form': form,
        'subject': subject,
    })


@login_required
@staff_required
def admin_manage_schedule(request, schedule_id=None):
    """Create or edit class schedule"""
    if schedule_id:
        try:
            schedule = ClassSchedule.objects.get(pk=schedule_id)
        except ClassSchedule.DoesNotExist:
            messages.error(request, 'Schedule not found.')
            return redirect('admin_portal_schedule')
    else:
        schedule = None

    if request.method == 'POST':
        from .forms import ScheduleForm
        form = ScheduleForm(request.POST, instance=schedule)
        if form.is_valid():
            form.save()
            messages.success(request, 'Schedule saved successfully!')
            return redirect('admin_portal_schedule')
    else:
        from .forms import ScheduleForm
        form = ScheduleForm(instance=schedule)

    return render(request, 'academics/admin_manage_schedule.html', {
        'form': form,
        'schedule': schedule,
    })
