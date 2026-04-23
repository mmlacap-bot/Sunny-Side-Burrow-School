from django.core.management.base import BaseCommand
from apps.student.models import GradeLevel

class Command(BaseCommand):
    help = 'Fix grade level ordering'

    def handle(self, *args, **kwargs):
        # Set proper ordering
        grades_order = [
            ('Kinder', 0),
            ('Grade 1', 1),
            ('Grade 2', 2),
            ('Grade 3', 3),
            ('Grade 4', 4),
            ('Grade 5', 5),
            ('Grade 6', 6),
            ('Preparatory', 7),
        ]
        
        for grade_name, order in grades_order:
            grade = GradeLevel.objects.filter(name=grade_name).first()
            if grade:
                grade.level_order = order
                grade.save()
                self.stdout.write(self.style.SUCCESS(f'Updated {grade_name} order to {order}'))

        # Verify final order
        self.stdout.write('\n=== Final Grade Level Order ===')
        grades = GradeLevel.objects.all().order_by('level_order')
        for grade in grades:
            self.stdout.write(f'{grade.level_order}: {grade.name}')
