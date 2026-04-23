from django.core.management.base import BaseCommand
from apps.student.models import GradeLevel, Subject, Section, ClassSchedule, SchoolYear
from datetime import time

class Command(BaseCommand):
    help = 'Fix grade levels: separate Kinder & Preparatory, and Grade 4-6 into individual grades'

    def handle(self, *args, **kwargs):
        # Get active school year
        school_year = SchoolYear.objects.filter(is_active=True).first()
        if not school_year:
            self.stdout.write(self.style.ERROR('No active school year found'))
            return

        # Delete old grade levels (Kindergarten, Grade 1, Grade 2, Grade 4, Grade 5, Grade 6)
        old_grades = ['Kindergarten', 'Grade 1', 'Grade 2', 'Grade 4', 'Grade 5', 'Grade 6']
        for grade_name in old_grades:
            grade = GradeLevel.objects.filter(name=grade_name).first()
            if grade:
                # Delete all sections, schedules, and subjects for this grade
                sections = Section.objects.filter(grade_level=grade)
                for section in sections:
                    ClassSchedule.objects.filter(section=section).delete()
                sections.delete()
                
                subjects = Subject.objects.filter(grade_level=grade)
                subjects.delete()
                
                grade.delete()
                self.stdout.write(self.style.SUCCESS(f'Deleted old grade level: {grade_name}'))

        # Update or create the new grade levels
        new_grades = [
            ('Kinder', 0),
            ('Preparatory', 1),
            ('Grade 1-2', 2),
            ('Grade 3', 3),
            ('Grade 4', 4),
            ('Grade 5', 5),
            ('Grade 6', 6),
        ]

        # Delete the old combined ones if they still exist
        for old_name in ['Kinder & Preparatory', 'Grade 4-6']:
            grade = GradeLevel.objects.filter(name=old_name).first()
            if grade:
                sections = Section.objects.filter(grade_level=grade)
                for section in sections:
                    ClassSchedule.objects.filter(section=section).delete()
                sections.delete()
                
                subjects = Subject.objects.filter(grade_level=grade)
                subjects.delete()
                
                grade.delete()
                self.stdout.write(self.style.SUCCESS(f'Deleted combined grade level: {old_name}'))

        # Get subject data
        subjects_data = {
            'Kinder': [
                ('MATH', 'Math', 3.0),
                ('SCI', 'Science', 2.0),
                ('ENG', 'English', 3.0),
                ('FIL', 'Filipino', 2.0),
                ('CL', 'Civic Literacy', 2.0),
            ],
            'Preparatory': [
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
            'Grade 4': [
                ('MATH', 'Math', 3.0),
                ('ENG', 'English', 3.0),
                ('FIL', 'Filipino', 3.0),
                ('SCI', 'Science', 3.0),
                ('MAPE', 'Music, Arts, Physical Education', 3.0),
                ('HELE', 'Health & Livelihood Education', 2.0),
                ('AP', 'Arts & Physical Education', 2.0),
                ('COMP', 'Computer', 2.0),
            ],
            'Grade 5': [
                ('MATH', 'Math', 3.0),
                ('ENG', 'English', 3.0),
                ('FIL', 'Filipino', 3.0),
                ('SCI', 'Science', 3.0),
                ('MAPE', 'Music, Arts, Physical Education', 3.0),
                ('HELE', 'Health & Livelihood Education', 2.0),
                ('AP', 'Arts & Physical Education', 2.0),
                ('COMP', 'Computer', 2.0),
            ],
            'Grade 6': [
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

        # Create or update grade levels and subjects
        for grade_name, level_order in new_grades:
            grade_level, created = GradeLevel.objects.get_or_create(
                name=grade_name,
                defaults={'level_order': level_order}
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created grade level: {grade_name}'))
            
            # Get subjects for this grade
            subject_list = subjects_data.get(grade_name, [])
            
            # Clear existing subjects for this grade
            Subject.objects.filter(grade_level=grade_level).delete()
            
            # Add subjects
            for code, name, units in subject_list:
                subject, created = Subject.objects.get_or_create(
                    name=name,
                    grade_level=grade_level,
                    defaults={'code': code, 'units': units}
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'  Created subject: {name}'))

            # Create sections
            for section_letter in ['A', 'B']:
                section, created = Section.objects.get_or_create(
                    name=f'Section {section_letter}',
                    grade_level=grade_level,
                    school_year=school_year,
                    defaults={'max_students': 40}
                )
                
                if created:
                    self.stdout.write(self.style.SUCCESS(f'  Created section: {section.name}'))
                    
                    # Create schedules for all subjects
                    subjects = Subject.objects.filter(grade_level=grade_level)
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
                                'room': f'{level_order + 1}-{section_letter}'
                            }
                        )

        self.stdout.write(self.style.SUCCESS('\n✓ Successfully reorganized all grade levels!'))
