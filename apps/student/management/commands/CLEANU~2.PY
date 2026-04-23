from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count

from apps.student.models import Enrollment


class Command(BaseCommand):
    help = "Clean enrolled students data: remove duplicate Enrollment records safely."

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Apply deletions. Without this flag, runs in dry-run mode.",
        )

    def handle(self, *args, **options):
        apply = bool(options.get("apply"))

        dup_groups = (
            Enrollment.objects.values("student_id", "school_year_id")
            .annotate(c=Count("id"))
            .filter(c__gt=1)
        )

        if not dup_groups.exists():
            self.stdout.write(self.style.SUCCESS("No duplicate Enrollment records found."))
            return

        self.stdout.write(self.style.WARNING(f"Found {dup_groups.count()} duplicate enrollment group(s)."))

        total_to_delete = 0
        with transaction.atomic():
            for group in dup_groups:
                student_id = group["student_id"]
                school_year_id = group["school_year_id"]

                enrollments = Enrollment.objects.filter(
                    student_id=student_id,
                    school_year_id=school_year_id,
                ).order_by("-enrolled_date", "-id")

                keep = enrollments.first()
                to_delete = enrollments.exclude(id=keep.id)
                count_delete = to_delete.count()
                total_to_delete += count_delete

                self.stdout.write(
                    f"- student={student_id} school_year={school_year_id}: keep Enrollment#{keep.id}, delete {count_delete}"
                )

                if apply and count_delete:
                    to_delete.delete()

            if not apply:
                transaction.set_rollback(True)

        if apply:
            self.stdout.write(self.style.SUCCESS(f"Deleted {total_to_delete} duplicate Enrollment record(s)."))
        else:
            self.stdout.write(self.style.WARNING(f"Dry-run only. Would delete {total_to_delete} Enrollment record(s)."))

