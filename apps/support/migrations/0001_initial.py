from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("student", "0005_teacher_subjects"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="MessageThread",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("student", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="message_threads", to="student.student")),
                ("teacher", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="message_threads", to="student.teacher")),
            ],
            options={
                "ordering": ["-updated_at"],
            },
        ),
        migrations.CreateModel(
            name="Message",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("body", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("read_by_student", models.BooleanField(default=False)),
                ("read_by_teacher", models.BooleanField(default=False)),
                ("sender", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="sent_messages", to=settings.AUTH_USER_MODEL)),
                ("thread", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="messages", to="support.messagethread")),
            ],
            options={
                "ordering": ["created_at"],
            },
        ),
        migrations.AddConstraint(
            model_name="messagethread",
            constraint=models.UniqueConstraint(fields=("student", "teacher"), name="unique_student_teacher_thread"),
        ),
    ]

