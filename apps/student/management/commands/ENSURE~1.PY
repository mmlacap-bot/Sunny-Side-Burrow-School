from django.core.management.base import BaseCommand
from apps.student.models import GradeLevel, Subject, Section, ClassSchedule, SchoolYear
from datetime import time

class Command(BaseCommand):
    help = 'Ensure all grade levels have sections and schedules'

    def handle(self, *args, **kwargs):
        school_year = SchoolYear.objects.filter(is_active=True).first()
        if not school_year:
            self.stdout.write(self.style.ERROR('No active school year found'))
            return

        # Ensure Grade 1-2 and Grade 3 exist and have sections
        grades_to_check = ['Grade 1-2', 'Grade 3']
        
        for grade_name in grades_to_check:
            grade = GradeLevel.objects.filter(name=grade_name).first()
            if grade:
                self.stdout.write(f'Processing {grade_name}...')
                
                # Check if sections exist
                sections = Section.objects.filter(grade_level=grade, school_year=school_year)
                if sections.count() == 0:
                    self.stdout.write(f'  Creating sections for {grade_name}...')
                    for section_letter in ['A', 'B']:
                        section, created = Section.objects.get_or_create(
                            name=f'Section {section_letter}',
                            grade_level=grade,
                            school_year=school_year,
                            defaults={'max_students': 40}
                        )
                        if created:
                            self.stdout.write(self.style.SUCCESS(f'    Created section: {section.name}'))
                
                # Create schedules for all subjects
                subjects = Subject.objects.filter(grade_level=grade)
                self.stdout.write(f'  Creating schedules for {subjects.count()} subjects...')
                
                days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']
                sections = Section.objects.filter(grade_level=grade)
                
                for section in sections:
                    existing_schedules = ClassSchedule.objects.filter(section=section).count()
                    if existing_schedules == 0:
                        for idx, subject in enumerate(subjects):
                            day = days[idx % len(days)]
                            hour = 8 + (idx // len(days))
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
                                    'room': f'{grade.level_order + 1}-{section.name[-1]}'
                                }
                            )
                            if created:
                                self.stdout.write(f'    Created schedule: {subject.name}')
            else:
                self.stdout.write(self.style.WARNING(f'{grade_name} not found'))

        self.stdout.write(self.style.SUCCESS('\n✓ All grade levels now have sections and schedules!'))
