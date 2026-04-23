import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('academics', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Enrollment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('Pending', 'Pending'), ('Enrolled', 'Enrolled'), ('Dropped', 'Dropped'), ('Transferred', 'Transferred')], default='Pending', max_length=20)),
                ('tuition_fee', models.DecimalField(decimal_places=2, default=10000, max_digits=10)),
                ('enrolled_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('notes', models.TextField(blank=True)),
                ('enrolled_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='enrolled_students', to=settings.AUTH_USER_MODEL)),
                ('grade_level', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='enrollments', to='academics.gradelevel')),
                ('school_year', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='enrollments', to='academics.schoolyear')),
                ('section', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='enrollments', to='academics.section')),
            ],
            options={
                'ordering': ['-enrolled_date'],
            },
        ),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('payment_date', models.DateField(default=django.utils.timezone.now)),
                ('payment_time', models.TimeField(default=django.utils.timezone.now)),
                ('payment_mode', models.CharField(choices=[('Cash', 'Cash'), ('Check', 'Check'), ('Online', 'Online Transfer'), ('Bank', 'Bank Deposit')], max_length=20)),
                ('reference_number', models.CharField(blank=True, max_length=50)),
                ('remarks', models.TextField(blank=True)),
                ('status', models.CharField(choices=[('PENDING', 'Pending'), ('CONFIRMED', 'Confirmed'), ('VOIDED', 'Voided')], default='PENDING', max_length=20)),
                ('void_reason', models.TextField(blank=True)),
                ('void_date', models.DateTimeField(blank=True, null=True)),
                ('enrollment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='student.enrollment')),
                ('received_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='payments_received', to=settings.AUTH_USER_MODEL)),
                ('voided_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='payments_voided', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-payment_date', '-payment_time'],
            },
        ),
        migrations.CreateModel(
            name='Professor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('employee_id', models.CharField(max_length=20, unique=True)),
                ('first_name', models.CharField(max_length=100)),
                ('last_name', models.CharField(max_length=100)),
                ('middle_name', models.CharField(blank=True, max_length=100, null=True)),
                ('birthdate', models.DateField()),
                ('gender', models.CharField(max_length=10)),
                ('address', models.TextField()),
                ('contact_number', models.CharField(max_length=20)),
                ('department', models.CharField(blank=True, max_length=100, null=True)),
                ('photo', models.ImageField(blank=True, null=True, upload_to='professor_photos/')),
                ('specialization', models.CharField(blank=True, max_length=100)),
                ('status', models.CharField(choices=[('Active', 'Active'), ('Inactive', 'Inactive')], default='Active', max_length=20)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='professor', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['last_name', 'first_name'],
            },
        ),
        migrations.CreateModel(
            name='Student',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('student_id', models.CharField(max_length=20, unique=True)),
                ('first_name', models.CharField(max_length=100)),
                ('last_name', models.CharField(max_length=100)),
                ('middle_name', models.CharField(blank=True, max_length=100)),
                ('birthdate', models.DateField()),
                ('gender', models.CharField(max_length=10)),
                ('address', models.TextField()),
                ('contact_number', models.CharField(max_length=15)),
                ('guardian_name', models.CharField(max_length=100)),
                ('guardian_contact', models.CharField(max_length=15)),
                ('photo', models.ImageField(blank=True, null=True, upload_to='student_photos/')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['last_name', 'first_name'],
            },
        ),
        migrations.AddField(
            model_name='enrollment',
            name='student',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='enrollments', to='student.student'),
        ),
        migrations.CreateModel(
            name='Concern',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subject_text', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('date_filed', models.DateTimeField(default=django.utils.timezone.now)),
                ('status', models.CharField(choices=[('Open', 'Open'), ('In Progress', 'In Progress'), ('Resolved', 'Resolved'), ('Closed', 'Closed')], default='Open', max_length=20)),
                ('response', models.TextField(blank=True)),
                ('date_responded', models.DateTimeField(blank=True, null=True)),
                ('date_resolved', models.DateTimeField(blank=True, null=True)),
                ('notes', models.TextField(blank=True)),
                ('resolved_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='concerns_resolved', to=settings.AUTH_USER_MODEL)),
                ('responded_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='concerns_responded', to=settings.AUTH_USER_MODEL)),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='concerns', to='student.student')),
            ],
            options={
                'ordering': ['-date_filed'],
            },
        ),
        migrations.CreateModel(
            name='EnrollmentSubject',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('Enrolled', 'Enrolled'), ('Dropped', 'Dropped'), ('Completed', 'Completed')], default='Enrolled', max_length=20)),
                ('grade', models.CharField(blank=True, max_length=5)),
                ('class_schedule', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='enrollments', to='academics.classschedule')),
                ('enrollment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subjects', to='student.enrollment')),
            ],
            options={
                'ordering': ['enrollment', 'class_schedule__day', 'class_schedule__time_start'],
                'unique_together': {('enrollment', 'class_schedule')},
            },
        ),
        migrations.AddConstraint(
            model_name='enrollment',
            constraint=models.UniqueConstraint(fields=('student', 'school_year'), name='unique_student_school_year_enrollment'),
        ),
    ]
