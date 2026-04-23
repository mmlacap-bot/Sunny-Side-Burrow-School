from django.core.management.base import BaseCommand
from apps.student.models import GradeLevel

class Command(BaseCommand):
    help = 'Reorder grade levels to place Preparatory after Kinder'

    def handle(self, *args, **kwargs):
        # Set proper ordering with Preparatory after Kinder
        grades_order = [
            ('Kinder', 0),
            ('Preparatory', 1),
            ('Grade 1', 2),
            ('Grade 2', 3),
            ('Grade 3', 4),
            ('Grade 4', 5),
            ('Grade 5', 6),
            ('Grade 6', 7),
        ]
        
        for grade_name, order in grades_order:
            grade = GradeLevel.objects.filter(name=grade_name).first()
            if grade:
                grade.level_order = order
                grade.save()
                self.stdout.write(self.style.SUCCESS(f'Updated {grade_name} order to {order}'))

        self.stdout.write(self.style.SUCCESS('\n=== Final Grade Level Order ==='))
        grades = GradeLevel.objects.all().order_by('level_order')
        for grade in grades:
            self.stdout.write(f'{grade.level_order}: {grade.name}')
