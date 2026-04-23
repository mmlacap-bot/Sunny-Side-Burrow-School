from datetime import date, time
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core import mail
from django.db import IntegrityError
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import ClassSchedule, Enrollment, EnrollmentSubject, GradeLevel, Payment, SchoolYear, Section, Student, Subject

User = get_user_model()


class EnrollmentSystemTests(TestCase):
    def setUp(self):
        self.school_year = SchoolYear.objects.create(year_start=2026, year_end=2027, is_active=True)
        self.grade_level = GradeLevel.objects.create(name='Grade 1', level_order=1)
        self.section = Section.objects.create(
            name='Section A',
            grade_level=self.grade_level,
            max_students=2,
            school_year=self.school_year,
        )
        self.subject = Subject.objects.create(
            name='Mathematics',
            code='MATH1',
            grade_level=self.grade_level,
            units=Decimal('3.00'),
        )

    def create_student(self, student_id='S-001', email='student1@example.com'):
        user = User.objects.create_user(
            username=email,
            email=email,
            password='TestPass123!',
            first_name='Student',
            last_name='User',
        )
        student = Student.objects.create(
            user=user,
            student_id=student_id,
            first_name='Student',
            last_name='User',
            middle_name='',
            birthdate=date(2010, 1, 1),
            gender='Female',
            address='Test Address',
            contact_number='09123456789',
            guardian_name='Guardian',
            guardian_contact='09987654321',
        )
        return user, student

    def login_student(self, login_email='student1@example.com', password='TestPass123!'):
        return self.client.post(reverse('home'), {'login_email': login_email, 'password': password})

    def create_full_schedule_set(self):
        return ClassSchedule.objects.create(
            subject=self.subject,
            section=self.section,
            day='Mon',
            time_start=time(8, 0),
            time_end=time(9, 0),
            room='Room 1',
            school_year=self.school_year,
        )

    def test_student_registration_creates_student_profile(self):
        response = self.client.post(
            reverse('register'),
            {
                'email': 'newstudent@example.com',
                'password': 'SecurePass123!',
                'confirm_password': 'SecurePass123!',
                'first_name': 'New',
                'last_name': 'Student',
                'middle_name': '',
                'birthdate': '2010-01-01',
                'gender': 'Female',
                'address': '123 Street',
                'contact_number': '09123456789',
                'guardian_name': 'Parent',
                'guardian_contact': '09987654321',
            },
            follow=True,
        )

        self.assertRedirects(response, reverse('home'))
        user = User.objects.get(first_name='New', last_name='Student')
        self.assertTrue(Student.objects.filter(user=user).exists())
        self.assertEqual(user.email, 'newstudent@example.com')
        self.assertTrue(user.username.endswith('@sunny.edu.ph'))
        self.assertRegex(user.username, r'\d+@sunny\.edu\.ph$')

    def test_public_registration_cannot_create_professor_account(self):
        self.client.post(
            reverse('register'),
            {
                'role': 'professor',
                'email': 'stillstudent@example.com',
                'password': 'SecurePass123!',
                'confirm_password': 'SecurePass123!',
                'first_name': 'Still',
                'last_name': 'Student',
                'middle_name': '',
                'birthdate': '2010-01-01',
                'gender': 'Male',
                'address': '123 Street',
                'contact_number': '09123456789',
                'guardian_name': 'Parent',
                'guardian_contact': '09987654321',
            },
        )

        user = User.objects.get(email='stillstudent@example.com')
        self.assertTrue(hasattr(user, 'student'))
        self.assertFalse(hasattr(user, 'professor'))

    def test_unique_enrollment_per_school_year_is_enforced(self):
        _, student = self.create_student()
        Enrollment.objects.create(
            student=student,
            school_year=self.school_year,
            grade_level=self.grade_level,
            section=self.section,
            tuition_fee=Decimal('10000.00'),
        )

        with self.assertRaises(IntegrityError):
            Enrollment.objects.create(
                student=student,
                school_year=self.school_year,
                grade_level=self.grade_level,
                section=self.section,
                tuition_fee=Decimal('10000.00'),
            )

    def test_enrollment_fails_when_section_is_full(self):
        _, first_student = self.create_student('S-001', 'student1@example.com')
        second_user, _ = self.create_student('S-002', 'student2@example.com')
        self.section.max_students = 1
        self.section.save()
        self.create_full_schedule_set()
        Enrollment.objects.create(
            student=first_student,
            school_year=self.school_year,
            grade_level=self.grade_level,
            section=self.section,
            status='Pending',
            tuition_fee=Decimal('10000.00'),
        )

        self.client.force_login(second_user)
        response = self.client.post(
            reverse('student_enrollment'),
            {
                'step': '2',
                'action': 'confirm',
                'school_year': str(self.school_year.id),
                'grade_level': str(self.grade_level.id),
                'section': str(self.section.id),
            },
        )

        self.assertContains(response, 'This section is already full.')
        self.assertEqual(Enrollment.objects.filter(student__user=second_user).count(), 0)

    def test_enrollment_creation_is_atomic_when_schedule_missing(self):
        user, _ = self.create_student()
        second_subject = Subject.objects.create(
            name='Science',
            code='SCI1',
            grade_level=self.grade_level,
            units=Decimal('3.00'),
        )
        ClassSchedule.objects.create(
            subject=self.subject,
            section=self.section,
            day='Mon',
            time_start=time(8, 0),
            time_end=time(9, 0),
            room='Room 1',
            school_year=self.school_year,
        )

        self.client.force_login(user)
        response = self.client.post(
            reverse('student_enrollment'),
            {
                'step': '2',
                'action': 'confirm',
                'school_year': str(self.school_year.id),
                'grade_level': str(self.grade_level.id),
                'section': str(self.section.id),
            },
        )

        self.assertContains(response, second_subject.name)
        self.assertEqual(Enrollment.objects.filter(student__user=user).count(), 0)
        self.assertEqual(EnrollmentSubject.objects.count(), 0)

    def test_payment_balance_calculation_uses_enrollment(self):
        user, student = self.create_student()
        enrollment = Enrollment.objects.create(
            student=student,
            school_year=self.school_year,
            grade_level=self.grade_level,
            section=self.section,
            tuition_fee=Decimal('12000.00'),
        )
        Payment.objects.create(enrollment=enrollment, amount=Decimal('2000.00'), payment_mode='Cash')
        Payment.objects.create(enrollment=enrollment, amount=Decimal('3500.00'), payment_mode='Online')

        self.client.force_login(user)
        response = self.client.get(reverse('student_payment'))

        self.assertEqual(response.context['total_paid'], Decimal('5500.00'))
        self.assertEqual(response.context['balance'], Decimal('6500.00'))
        self.assertEqual(response.context['status'], 'Partial')
