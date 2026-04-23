from django.core.management.base import BaseCommand
from apps.student.models import SchoolYear, GradeLevel, Section, Subject, ClassSchedule
from datetime import time

class Command(BaseCommand):
    help = 'Create sample sections and class schedules'

    def handle(self, *args, **kwargs):
        # Get active school year or create one
        school_year, created = SchoolYear.objects.get_or_create(
            year_start=2026,
            year_end=2027,
            defaults={'is_active': True}
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created school year: {school_year}'))

        # Create sections for each grade level
        grade_levels = GradeLevel.objects.all()
        for grade in grade_levels:
            for i in range(1, 3):  # Create 2 sections per grade
                section, created = Section.objects.get_or_create(
                    name=f'Section {chr(64+i)}',  # A, B, C...
                    grade_level=grade,
                    school_year=school_year,
                    defaults={'max_students': 40}
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Created section: {section}'))
                    
                    # Create schedules for all subjects in this grade
                    subjects = Subject.objects.filter(grade_level=grade)
                    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']
                    
                    for idx, subject in enumerate(subjects):
                        day = days[idx % len(days)]
                        
                        # Assign different time slots
                        hour = 8 + (idx // len(days))  # 8 AM, 9 AM, 10 AM, etc.
                        time_start = time(hour, 0)
                        time_end = time(hour + 1, 0)
                        
                        schedule, created = ClassSchedule.objects.get_or_create(
                            subject=subject,
                            section=section,
                            school_year=school_year,
                            defaults={
                                'day': day,
                                'time_start': time_start,
                                'time_end': time_end,
                                'room': f'{grade.level_order + 1}-{chr(64+i)}'  # Room numbering
                            }
                        )
                        if created:
                            self.stdout.write(self.style.SUCCESS(f'Created schedule: {subject.name} - {section.name}'))

        self.stdout.write(self.style.SUCCESS('Successfully created sections and schedules!'))
