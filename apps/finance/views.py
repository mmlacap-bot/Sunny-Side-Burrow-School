from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import redirect, render

from apps.student.models import Enrollment, Payment, Student
from .forms import StudentPaymentSubmissionForm

staff_required = user_passes_test(lambda u: u.is_staff)


@login_required
def student_payment(request):
    try:
        student = request.user.student
    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found. Please contact administrator.')
        return redirect('home')

    enrollment = Enrollment.objects.filter(student=student, school_year__is_active=True).first()

    if request.method == 'POST':
        if not enrollment:
            messages.error(request, 'No active enrollment found for payment.')
            return redirect('student_payment')
        if enrollment.balance <= 0:
            messages.info(request, 'Your enrollment is already fully paid.')
            return redirect('student_payment')

        form = StudentPaymentSubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            payment_amount = form.cleaned_data['amount']
            payment = Payment.objects.create(
                enrollment=enrollment,
                amount=payment_amount,
                payment_mode=form.cleaned_data['payment_mode'],
                reference_number=form.cleaned_data['reference_number'],
                proof_of_payment=form.cleaned_data['proof_of_payment'],
                remarks='Student-submitted payment with proof of payment.',
            )
            payment.confirm_payment(request.user)
            messages.success(
                request,
                f'Payment submitted successfully. Transaction #{payment.id} has been recorded as Paid.'
            )
            return redirect('student_payment')
    else:
        form = StudentPaymentSubmissionForm()

    payments = enrollment.payments.order_by('-payment_date') if enrollment else Payment.objects.none()
    total_paid = enrollment.total_paid if enrollment else 0
    balance = enrollment.balance if enrollment else 0
    status = enrollment.payment_status if enrollment else 'Unpaid'
    tuition_fee = enrollment.tuition_fee if enrollment else 0
    return render(
        request,
        'finance/student_payment.html',
        {
            'payments': payments,
            'total_paid': total_paid,
            'balance': balance,
            'status': status,
            'tuition_fee': tuition_fee,
            'enrollment': enrollment,
            'form': form,
        },
    )


@login_required
@staff_required
def admin_portal_payment(request):
    payments = Payment.objects.select_related('enrollment__student__user')
    return render(request, 'finance/admin_portal_payment.html', {'payments': payments})


@login_required
@staff_required
def admin_process_payment(request, enrollment_id):
    """Record and confirm payment for an enrollment"""
    try:
        enrollment = Enrollment.objects.get(pk=enrollment_id)
    except Enrollment.DoesNotExist:
        messages.error(request, 'Enrollment not found.')
        return redirect('admin_portal_payment')

    if request.method == 'POST':
        from .forms import PaymentForm
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.enrollment = enrollment
            payment.save()
            payment.confirm_payment(request.user)
            messages.success(request, 'Payment recorded successfully!')
            return redirect('admin_portal_payment')
    else:
        from .forms import PaymentForm
        form = PaymentForm()

    return render(request, 'finance/admin_process_payment.html', {
        'form': form,
        'enrollment': enrollment,
        'balance': enrollment.balance,
    })


@login_required
@staff_required
def admin_void_payment(request, payment_id):
    """Void a payment"""
    try:
        payment = Payment.objects.get(pk=payment_id)
    except Payment.DoesNotExist:
        messages.error(request, 'Payment not found.')
        return redirect('admin_portal_payment')

    if payment.status == 'VOIDED':
        messages.error(request, 'This payment is already voided.')
        return redirect('admin_portal_payment')

    if request.method == 'POST':
        from .forms import VoidPaymentForm
        form = VoidPaymentForm(request.POST)
        if form.is_valid():
            reason = form.cleaned_data['void_reason']
            try:
                payment.void_payment(request.user, reason)
                messages.success(request, 'Payment voided successfully!')
                return redirect('admin_portal_payment')
            except Exception as e:
                messages.error(request, f'Error: {str(e)}')
    else:
        from .forms import VoidPaymentForm
        form = VoidPaymentForm()

    return render(request, 'finance/admin_void_payment.html', {
        'form': form,
        'payment': payment,
    })


@login_required
@staff_required
def admin_confirm_payment(request, payment_id):
    """Confirm a pending payment"""
    try:
        payment = Payment.objects.get(pk=payment_id)
    except Payment.DoesNotExist:
        messages.error(request, 'Payment not found.')
        return redirect('admin_portal_payment')

    if request.method == 'POST':
        try:
            payment.confirm_payment(request.user)
            messages.success(request, 'Payment confirmed successfully!')
            return redirect('admin_portal_payment')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')

    return render(request, 'finance/admin_confirm_payment.html', {'payment': payment})
