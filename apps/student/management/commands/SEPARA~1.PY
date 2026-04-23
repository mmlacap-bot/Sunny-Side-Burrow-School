from django.core.management.base import BaseCommand
from apps.student.models import GradeLevel, Subject, Section, ClassSchedule, SchoolYear
from datetime import time

class Command(BaseCommand):
    help = 'Separate Grade 1-2 into Grade 1 and Grade 2'

    def handle(self, *args, **kwargs):
        school_year = SchoolYear.objects.filter(is_active=True).first()
        if not school_year:
            self.stdout.write(self.style.ERROR('No active school year found'))
            return

        # Get the current Grade 1-2
        grade_1_2 = GradeLevel.objects.filter(name='Grade 1-2').first()
        if not grade_1_2:
            self.stdout.write(self.style.ERROR('Grade 1-2 not found'))
            return

        # Get subjects from Grade 1-2
        subjects_data = [
            ('MATH', 'Math', 3.0),
            ('ENG', 'English', 3.0),
            ('FIL', 'Filipino', 3.0),
            ('MAK', 'Makabansa', 2.0),
            ('MAPE', 'Music, Arts, Physical Education', 3.0),
            ('CL', 'Civic Literacy', 2.0),
        ]

        # Delete the old Grade 1-2 sections and schedules but keep subjects
        old_sections = Section.objects.filter(grade_level=grade_1_2)
        for section in old_sections:
            ClassSchedule.objects.filter(section=section).delete()
            section.delete()
        self.stdout.write(self.style.SUCCESS('Deleted old Grade 1-2 sections'))

        # Update Grade 1-2 to Grade 1
        grade_1_2.name = 'Grade 1'
        grade_1_2.level_order = 1
        grade_1_2.save()
        self.stdout.write(self.style.SUCCESS('✓ Renamed to Grade 1'))

        # Create Grade 2 with same order + 0.5 so it appears after Grade 1
        grade_2, created = GradeLevel.objects.get_or_create(
            name='Grade 2',
            defaults={'level_order': 2}
        )
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Created Grade 2'))

        # Clear any existing subjects and schedules for both grades
        Subject.objects.filter(grade_level=grade_1_2).delete()
        Subject.objects.filter(grade_level=grade_2).delete()
        Section.objects.filter(grade_level=grade_2).delete()

        # Add subjects to both Grade 1 and Grade 2
        for code, name, units in subjects_data:
            # Grade 1
            Subject.objects.get_or_create(
                name=name,
                grade_level=grade_1_2,
                defaults={'code': code, 'units': units}
            )
            # Grade 2
            Subject.objects.get_or_create(
                name=name,
                grade_level=grade_2,
                defaults={'code': code, 'units': units}
            )

        self.stdout.write(self.style.SUCCESS(f'✓ Added {len(subjects_data)} subjects to both grades'))

        # Create sections for both grades
        for grade in [grade_1_2, grade_2]:
            for section_letter in ['A', 'B']:
                section, created = Section.objects.get_or_create(
                    name=f'Section {section_letter}',
                    grade_level=grade,
                    school_year=school_year,
                    defaults={'max_students': 40}
                )

                if created:
                    self.stdout.write(f'  Created section: {grade.name} - {section.name}')

                    # Create schedules for all subjects
                    subjects = Subject.objects.filter(grade_level=grade)
                    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']

                    for idx, subject in enumerate(subjects):
                        day = days[idx % len(days)]
                        hour = 8 + (idx // len(days))
                        time_start = time(hour, 0)
                        time_end = time(hour + 1, 0)

                        ClassSchedule.objects.get_or_create(
                            subject=subject,
                            section=section,
                            school_year=school_year,
                            defaults={
                                'day': day,
                                'time_start': time_start,
                                'time_end': time_end,
                                'room': f'{grade.level_order + 1}-{section_letter}'
                            }
                        )

        self.stdout.write(self.style.SUCCESS('\n✓ Successfully separated Grade 1-2 into Grade 1 and Grade 2!'))
