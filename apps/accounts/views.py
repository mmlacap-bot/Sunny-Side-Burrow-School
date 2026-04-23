import datetime
import logging
import random

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.mail import send_mail
from django.db import IntegrityError, transaction
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie

logger = logging.getLogger(__name__)

from django.utils import timezone
from .forms import (
    LoginForm, TeacherRegistrationForm, StudentRegistrationForm,
    ChangePasswordForm, UpdateEmailForm, MFASettingsForm,
    OTPVerifyForm, SecurityQuestionVerifyForm
)

User = get_user_model()
staff_required = user_passes_test(lambda u: u.is_staff)


def send_otp_email(user):
    """Generates and sends an OTP to the user's registered email"""
    otp = str(random.randint(100000, 999999))
    user.last_otp = otp
    user.otp_expiry = timezone.now() + datetime.timedelta(minutes=10)
    user.save()
    
    subject = 'Your Security Verification Code'
    message = f'Hello {user.first_name},\n\nYour verification code is: {otp}\n\nThis code will expire in 10 minutes.'
    
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
        return True
    except Exception as e:
        logger.error(f"Failed to send OTP email: {e}")
        return False


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


def logout_view(request):
    logout(request)
    return redirect('home')


def forgot_password(request):
    if request.method == 'POST':
        messages.success(request, 'If an account with that email exists, a password reset link has been sent.')
        return redirect('home')
    return render(request, 'accounts/forgot_password.html')


def home(request):
    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        role = form.cleaned_data['role']
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']
        authenticated_user = authenticate(request, username=email, password=password)

        if authenticated_user is not None:
            account_role = None
            if hasattr(authenticated_user, 'student'):
                account_role = 'student'
            elif authenticated_user.is_staff and hasattr(authenticated_user, 'teacher'):
                account_role = 'teacher'
            elif authenticated_user.is_staff:
                account_role = 'administrator'

            if account_role and account_role != role:
                role_name = account_role.capitalize() if account_role != 'administrator' else 'Administrator'
                return render(
                    request,
                    'accounts/home.html',
                    {
                        'form': form,
                        'error': f'This account is registered as {role_name}. Please select the correct role before logging in.',
                    },
                )

            # Verification logic for Students and Teachers
            if role in ['student', 'teacher']:
                if role == 'student' and not hasattr(authenticated_user, 'student'):
                    return render(request, 'accounts/home.html', {'form': form, 'error': 'Student profile not found.'})
                if role == 'teacher' and not (authenticated_user.is_staff and hasattr(authenticated_user, 'teacher')):
                    return render(request, 'accounts/home.html', {'form': form, 'error': 'Teacher profile not found.'})
                
                # Check for MFA
                if authenticated_user.mfa_type != 'NONE':
                    request.session['pre_auth_user_id'] = authenticated_user.id
                    request.session['target_role'] = role
                    
                    if authenticated_user.mfa_type == 'OTP':
                        if send_otp_email(authenticated_user):
                            messages.info(request, f'A verification code has been sent to {authenticated_user.email}.')
                            return redirect('mfa_verify')
                        else:
                            return render(request, 'accounts/home.html', {'form': form, 'error': 'Failed to send verification code. Please contact support.'})
                    
                    if authenticated_user.mfa_type == 'QUESTION':
                        question = authenticated_user.get_random_security_question()
                        if question:
                            request.session['mfa_question_id'] = question.id
                            return redirect('mfa_question')
                        else:
                            return render(request, 'accounts/home.html', {'form': form, 'error': 'No security questions configured. Please contact support.'})

                # No MFA or MFA bypassed (Admins)
                login(request, authenticated_user)
                return redirect(f'{role}_dashboard')

            if role == 'administrator':
                if not authenticated_user.is_staff or hasattr(authenticated_user, 'teacher'):
                    return render(request, 'accounts/home.html', {'form': form, 'error': 'Administrator account not found.'})
                login(request, authenticated_user)
                return redirect('admin_portal_dashboard')

        return render(request, 'accounts/home.html', {'form': form, 'error': 'Invalid credentials or role selected.'})

    return render(request, 'accounts/home.html', {'form': form})


def register(request):
    role = request.POST.get('role', 'student') if request.method == 'POST' else 'student'
    form = StudentRegistrationForm(request.POST or None) if role == 'student' else TeacherRegistrationForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
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
                    is_staff=(role == 'teacher' or role == 'professor'), # Handle both for safety
                )
                if role == 'student':
                    from apps.student.models import Student
                    student = Student.objects.create(
                        user=user,
                        first_name=data['first_name'],
                        last_name=data['last_name'],
                        middle_name=data.get('middle_name', ''),
                        birthdate=data['birthdate'],
                        gender=data['gender'],
                        address=data.get('address', ''),
                        contact_number=data.get('contact_number', ''),
                        guardian_name=data.get('guardian_name', ''),
                        guardian_contact=data.get('guardian_contact', ''),
                    )
                    id_label = 'Student ID'
                    generated_id = student.student_id
                else:
                    from apps.student.models import Teacher
                    teacher = Teacher.objects.create(
                        user=user,
                        first_name=data['first_name'],
                        last_name=data['last_name'],
                        middle_name=data.get('middle_name', ''),
                        birthdate=data['birthdate'],
                        gender=data['gender'],
                        address=data.get('address', ''),
                        contact_number=data.get('contact_number', ''),
                        employee_id=data.get('employee_id', ''),
                    )
                    id_label = 'Teacher ID'
                    generated_id = teacher.employee_id
        except IntegrityError:
            form.add_error('email', 'A user with this email already exists.')
        else:
            subject = 'Sunny Side Burrow School Registration Details'
            message = (
                f'Hello {data["first_name"]} {data["last_name"]},\n\n'
                f'Thank you for registering. Your account has been created with the following details:\n\n'
                f'Automated login email: {login_email}\n'
                f'{id_label}: {generated_id}\n\n'
                'Use the automated email above to log in to the portal.\n\n'
                'If you did not request this registration, please contact support.'
            )
            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [contact_email],
                )
            except Exception as exc:
                logger.exception('Failed to send registration email')
                messages.error(
                    request,
                    'Registration completed, but the automated email could not be sent. '
                    f'Please check SMTP settings or contact support. ({exc})',
                )
            else:
                messages.success(
                    request,
                    f'Registration successful. Your generated login email is {login_email} and has been sent to {contact_email}. '
                    'Use that email to sign in to the portal.',
                )
            return redirect('home')

    return render(request, 'accounts/register.html', {'form': form, 'selected_role': role})


@login_required
def account_details(request):
    """View and edit account details"""
    if hasattr(request.user, 'student'):
        student = request.user.student
        if request.method == 'POST':
            from .forms import StudentProfileForm
            form = StudentProfileForm(request.POST, request.FILES, instance=student)
            if form.is_valid():
                form.save()
                messages.success(request, 'Profile updated successfully!')
                return redirect('account_details')
        else:
            from .forms import StudentProfileForm
            form = StudentProfileForm(instance=student)
        
        return render(request, 'accounts/account_details.html', {
            'form': form,
            'student': student,
            'user_type': 'student'
        })
    
    elif hasattr(request.user, 'teacher'):
        teacher = request.user.teacher
        if request.method == 'POST':
            from .forms import TeacherProfileForm
            form = TeacherProfileForm(request.POST, request.FILES, instance=teacher)
            if form.is_valid():
                form.save()
                messages.success(request, 'Profile updated successfully!')
                return redirect('account_details')
        else:
            from .forms import TeacherProfileForm
            form = TeacherProfileForm(instance=teacher)
        
        return render(request, 'accounts/account_details.html', {
            'form': form,
            'teacher': teacher,
            'user_type': 'teacher'
        })
    
    messages.error(request, 'No profile found.')
    return redirect('home')


@login_required
def change_password(request):
    """Change password view"""
    if request.method == 'POST':
        from .forms import ChangePasswordForm
        form = ChangePasswordForm(request.POST, user=request.user)
        if form.is_valid():
            request.user.set_password(form.cleaned_data['new_password'])
            request.user.save()
            # Update session to prevent logout
            from django.contrib.auth import update_session_auth_hash
            update_session_auth_hash(request, request.user)
            messages.success(request, 'Password changed successfully!')
            return redirect('account_details')
    else:
        from .forms import ChangePasswordForm
        form = ChangePasswordForm()
    
    
    # Determine which base template to use
    base_template = 'base_teacher.html' if hasattr(request.user, 'teacher') else 'base_student.html'
    
    return render(request, 'accounts/change_password.html', {'form': form, 'base_template': base_template})


@login_required
@ensure_csrf_cookie
@csrf_protect
def settings_view(request):
    """Unified settings for password, email, and MFA"""
    if request.user.is_staff and not hasattr(request.user, 'teacher'):
        messages.warning(request, 'Security settings are currently only available for Students and Teachers.')
        return redirect('admin_portal_dashboard')

    password_form = ChangePasswordForm(user=request.user)
    email_form = UpdateEmailForm(user=request.user, initial={'email': request.user.email})
    
    # Pre-populate MFA form if they have questions
    initial_mfa = {'mfa_type': request.user.mfa_type}
    existing_questions = request.user.security_questions.all()
    for i, q_obj in enumerate(existing_questions, 1):
        if i > 8: break # Safety
        initial_mfa[f'question_{i}'] = q_obj.question_text
        # We don't pre-populate answers for security

    mfa_form = MFASettingsForm(initial=initial_mfa)

    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        
        if form_type == 'password':
            password_form = ChangePasswordForm(request.POST, user=request.user)
            if password_form.is_valid():
                request.user.set_password(password_form.cleaned_data['new_password'])
                request.user.save()
                from django.contrib.auth import update_session_auth_hash
                update_session_auth_hash(request, request.user)
                messages.success(request, 'Password changed successfully!')
                return redirect('settings')
                
        elif form_type == 'email':
            email_form = UpdateEmailForm(request.POST, user=request.user)
            if email_form.is_valid():
                request.user.email = email_form.cleaned_data['email']
                request.user.save()
                messages.success(request, 'Registered email updated successfully!')
                return redirect('settings')
                
        elif form_type == 'mfa':
            mfa_form = MFASettingsForm(request.POST)
            if mfa_form.is_valid():
                request.user.mfa_type = mfa_form.cleaned_data['mfa_type']
                if request.user.mfa_type == 'QUESTION':
                    from .models import SecurityQuestion
                    # Clear old ones and save 8 new ones
                    request.user.security_questions.all().delete()
                    for i in range(1, 9):
                        q_text = mfa_form.cleaned_data[f'question_{i}']
                        a_text = mfa_form.cleaned_data[f'answer_{i}']
                        sq = SecurityQuestion.objects.create(
                            user=request.user,
                            question_text=q_text
                        )
                        sq.set_answer(a_text)
                        sq.save()
                
                request.user.save()
                messages.success(request, 'MFA settings updated successfully!')
                return redirect('settings')

    # Determine which base template to use
    base_template = 'base_teacher.html' if hasattr(request.user, 'teacher') else 'base_student.html'

    return render(request, 'accounts/settings.html', {
        'password_form': password_form,
        'email_form': email_form,
        'mfa_form': mfa_form,
        'base_template': base_template,
    })


def mfa_verify(request):
    """View to verify OTP code during login"""
    user_id = request.session.get('pre_auth_user_id')
    if not user_id:
        return redirect('home')
        
    user = User.objects.get(id=user_id)
    form = OTPVerifyForm(request.POST or None)
    
    if request.method == 'POST' and form.is_valid():
        code = form.cleaned_data['otp_code']
        if user.last_otp == code and user.otp_expiry > timezone.now():
            # Clear pre-auth data
            del request.session['pre_auth_user_id']
            role = request.session.pop('target_role', 'student')
            login(request, user)
            return redirect(f'{role}_dashboard')
        else:
            messages.error(request, 'Invalid or expired verification code.')
            
    return render(request, 'accounts/mfa_verify.html', {
        'form': form, 
        'user': user,
        'otp_expiry_iso': user.otp_expiry.isoformat() if user.otp_expiry else None
    })


def mfa_question(request):
    """View to verify a randomly selected security question during login"""
    user_id = request.session.get('pre_auth_user_id')
    question_id = request.session.get('mfa_question_id')
    
    if not user_id or not question_id:
        return redirect('home')
        
    user = User.objects.get(id=user_id)
    from .models import SecurityQuestion
    try:
        question = SecurityQuestion.objects.get(id=question_id, user=user)
    except SecurityQuestion.DoesNotExist:
        return redirect('home')

    form = SecurityQuestionVerifyForm(request.POST or None)
    
    if request.method == 'POST' and form.is_valid():
        answer = form.cleaned_data['answer']
        if question.check_answer(answer):
            # Verification successful
            del request.session['pre_auth_user_id']
            del request.session['mfa_question_id']
            role = request.session.pop('target_role', 'student')
            login(request, user)
            messages.success(request, f'Welcome back, {user.first_name}!')
            return redirect(f'{role}_dashboard')
        else:
            messages.error(request, 'Incorrect answer. Please try again.')
            
    return render(request, 'accounts/mfa_question.html', {
        'form': form, 
        'question': question.question_text,
        'step': 1, # Template expects 'step', we'll hardcode 1
    })

