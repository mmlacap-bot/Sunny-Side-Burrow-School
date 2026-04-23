from django.core.management.base import BaseCommand
from apps.student.models import GradeLevel, Subject, Section, ClassSchedule

class Command(BaseCommand):
    help = 'Verify and display current grade levels, sections, and subjects'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('\n=== GRADE LEVELS STRUCTURE ===\n'))
        
        grade_levels = GradeLevel.objects.all().order_by('level_order')
        
        for grade in grade_levels:
            subjects = Subject.objects.filter(grade_level=grade)
            sections = Section.objects.filter(grade_level=grade)
            
            self.stdout.write(self.style.SUCCESS(f'📚 {grade.name} (Order: {grade.level_order})'))
            self.stdout.write(f'   Subjects ({subjects.count()}): {", ".join([s.name for s in subjects])}')
            self.stdout.write(f'   Sections ({sections.count()}):')
            
            for section in sections:
                schedules = ClassSchedule.objects.filter(section=section)
                self.stdout.write(f'      - {section.name} ({schedules.count()} schedules)')
            
            self.stdout.write('')
        
        self.stdout.write(self.style.SUCCESS('\n=== SUMMARY ==='))
        self.stdout.write(f'Total Grade Levels: {GradeLevel.objects.count()}')
        self.stdout.write(f'Total Subjects: {Subject.objects.count()}')
        self.stdout.write(f'Total Sections: {Section.objects.count()}')
        self.stdout.write(f'Total Schedules: {ClassSchedule.objects.count()}')
