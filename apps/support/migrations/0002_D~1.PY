from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("support", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="DirectThread",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user1", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="direct_threads_as_user1", to=settings.AUTH_USER_MODEL)),
                ("user2", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="direct_threads_as_user2", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["-updated_at"],
            },
        ),
        migrations.CreateModel(
            name="DirectMessage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("body", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("status", models.CharField(choices=[("SENT", "Sent"), ("READ", "Read")], default="SENT", max_length=10)),
                ("read_at", models.DateTimeField(blank=True, null=True)),
                ("receiver", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="direct_messages_received", to=settings.AUTH_USER_MODEL)),
                ("sender", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="direct_messages_sent", to=settings.AUTH_USER_MODEL)),
                ("thread", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="messages", to="support.directthread")),
            ],
            options={
                "ordering": ["created_at"],
            },
        ),
        migrations.AddConstraint(
            model_name="directthread",
            constraint=models.UniqueConstraint(fields=("user1", "user2"), name="unique_direct_thread_pair"),
        ),
    ]

