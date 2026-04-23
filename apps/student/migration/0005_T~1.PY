from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("academics", "0005_classschedule_teacher_alter_section_teacher"),
        ("student", "0004_delete_professor"),
    ]

    operations = [
        migrations.AddField(
            model_name="teacher",
            name="subjects",
            field=models.ManyToManyField(blank=True, related_name="teachers", to="academics.subject"),
        ),
    ]

