from django.core.management.base import BaseCommand
from apps.student.models import GradeLevel, Section, ClassSchedule

class Command(BaseCommand):
    help = 'Clean up duplicate sections and fix grade level ordering'

    def handle(self, *args, **kwargs):
        # Fix Preparatory order
        preparatory = GradeLevel.objects.filter(name='Preparatory').first()
        if preparatory:
            preparatory.level_order = 2
            preparatory.save()
            self.stdout.write(self.style.SUCCESS('✓ Updated Preparatory level_order to 2'))

        # Delete duplicate sections in Grade 3
        grade_3 = GradeLevel.objects.filter(name='Grade 3').first()
        if grade_3:
            # Get sections that are named just "A" or "B" without "Section " prefix
            duplicate_sections = Section.objects.filter(grade_level=grade_3).exclude(name__startswith='Section')
            
            if duplicate_sections.exists():
                count = duplicate_sections.count()
                for section in duplicate_sections:
                    # Delete associated schedules first
                    ClassSchedule.objects.filter(section=section).delete()
                    section.delete()
                self.stdout.write(self.style.SUCCESS(f'✓ Deleted {count} duplicate sections from Grade 3'))
            else:
                self.stdout.write('✓ No duplicate sections found in Grade 3')

        self.stdout.write(self.style.SUCCESS('\n✓ Cleanup completed successfully!'))
