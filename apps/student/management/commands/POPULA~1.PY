from django.core.management.base import BaseCommand
from apps.student.models import GradeLevel, Subject

class Command(BaseCommand):
    help = 'Populate subjects for each grade level'

    def handle(self, *args, **kwargs):
        # Define subjects by grade level
        subjects_data = {
            'Kinder & Preparatory': [
                ('MATH', 'Math', 3.0),
                ('SCI', 'Science', 2.0),
                ('ENG', 'English', 3.0),
                ('FIL', 'Filipino', 2.0),
                ('CL', 'Civic Literacy', 2.0),
            ],
            'Grade 1-2': [
                ('MATH', 'Math', 3.0),
                ('ENG', 'English', 3.0),
                ('FIL', 'Filipino', 3.0),
                ('MAK', 'Makabansa', 2.0),
                ('MAPE', 'Music, Arts, Physical Education', 3.0),
                ('CL', 'Civic Literacy', 2.0),
            ],
            'Grade 3': [
                ('MATH', 'Math', 3.0),
                ('ENG', 'English', 3.0),
                ('FIL', 'Filipino', 3.0),
                ('SCI', 'Science', 3.0),
                ('MAPE', 'Music, Arts, Physical Education', 3.0),
                ('MAK', 'Makabansa', 2.0),
                ('CL', 'Civic Literacy', 2.0),
            ],
            'Grade 4-6': [
                ('MATH', 'Math', 3.0),
                ('ENG', 'English', 3.0),
                ('FIL', 'Filipino', 3.0),
                ('SCI', 'Science', 3.0),
                ('MAPE', 'Music, Arts, Physical Education', 3.0),
                ('HELE', 'Health & Livelihood Education', 2.0),
                ('AP', 'Arts & Physical Education', 2.0),
                ('COMP', 'Computer', 2.0),
            ],
        }

        for grade_name, subjects in subjects_data.items():
            # Get or create the grade level
            grade_level, created = GradeLevel.objects.get_or_create(
                name=grade_name,
                defaults={'level_order': self._get_order(grade_name)}
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f'Created grade level: {grade_name}'))

            # Add subjects for this grade level
            for code, name, units in subjects:
                subject, created = Subject.objects.get_or_create(
                    name=name,
                    grade_level=grade_level,
                    defaults={'code': code, 'units': units}
                )
                
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Created subject: {name} for {grade_name}'))
                else:
                    self.stdout.write(f'Subject already exists: {name} for {grade_name}')

        self.stdout.write(self.style.SUCCESS('Successfully populated subjects!'))

    def _get_order(self, grade_name):
        order_map = {
            'Kinder & Preparatory': 0,
            'Grade 1-2': 1,
            'Grade 3': 2,
            'Grade 4-6': 3,
        }
        return order_map.get(grade_name, 999)
