"""
Management command to seed the database with initial data.

Usage:
    python manage.py seed_data
    python manage.py seed_data --clear  # Reset data before seeding
"""

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from apps.academics.models import SchoolYear, GradeLevel, Section, Subject, ClassSchedule
from apps.student.models import Teacher
import datetime


class Command(BaseCommand):
    help = 'Seed the database with initial default data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before seeding',
        )

    def handle(self, *args, **options):
        # Default capacity will be overridden by grade-specific logic
        
        if options['clear']:
            self.clear_data()
            self.stdout.write(self.style.WARNING('Cleared existing data.'))

        try:
            # Create default school year
            school_year = self.create_school_year()
            self.stdout.write(self.style.SUCCESS(f'[OK] Created School Year: {school_year}'))

            # Create grade levels
            grade_levels = self.create_grade_levels()
            self.stdout.write(self.style.SUCCESS(f'[OK] Created {len(grade_levels)} Grade Levels'))

            # Create sections
            sections = self.create_sections(school_year, grade_levels)
            self.stdout.write(self.style.SUCCESS(f'[OK] Created {len(sections)} Sections'))

            # Create subjects
            subjects = self.create_subjects(grade_levels)
            self.stdout.write(self.style.SUCCESS(f'[OK] Created {len(subjects)} Subjects'))

            # Create class schedules
            schedules = self.create_schedules(school_year, sections, subjects)
            self.stdout.write(self.style.SUCCESS(f'[OK] Created {len(schedules)} Class Schedules'))

            self.stdout.write(self.style.SUCCESS('\n[SUCCESS] Database seeding completed successfully!'))
            self.stdout.write(self.style.WARNING('\nNote: Create admin user and teachers using the admin panel or:'))
            self.stdout.write('  python manage.py createsuperuser')

        except Exception as e:
            raise CommandError(f'Error during seeding: {str(e)}')

    def clear_data(self):
        """Clear existing data"""
        ClassSchedule.objects.all().delete()
        Subject.objects.all().delete()
        Section.objects.all().delete()
        GradeLevel.objects.all().delete()
        SchoolYear.objects.all().delete()

    def create_school_year(self):
        """Create default school year"""
        current_year = datetime.date.today().year
        
        sy, created = SchoolYear.objects.get_or_create(
            year_start=current_year,
            year_end=current_year + 1,
            defaults={'is_active': True}
        )
        
        if created:
            # Deactivate other school years
            SchoolYear.objects.exclude(pk=sy.pk).update(is_active=False)
        
        return sy

    def create_grade_levels(self):
        """Create all grade levels"""
        grades = [
            {'name': 'Kinder', 'level_order': 1},
            {'name': 'Preparatory', 'level_order': 2},
            {'name': 'Grade 1', 'level_order': 3},
            {'name': 'Grade 2', 'level_order': 4},
            {'name': 'Grade 3', 'level_order': 5},
            {'name': 'Grade 4', 'level_order': 6},
            {'name': 'Grade 5', 'level_order': 7},
            {'name': 'Grade 6', 'level_order': 8},
        ]

        created_grades = []
        for grade_data in grades:
            grade, created = GradeLevel.objects.get_or_create(name=grade_data['name'], defaults={'level_order': grade_data['level_order']})
            created_grades.append(grade)

        return created_grades

    def create_sections(self, school_year, grade_levels):
        """Create sections for each grade level"""
        created_sections = []
        
        for grade in grade_levels:
            # Set limits: Kinder/Prep = 15, Grade 1-6 = 25
            if grade.name in ['Kinder', 'Preparatory']:
                max_students = 15
            else:
                max_students = 25

            for section_name in ['A', 'B']:
                section, created = Section.objects.get_or_create(
                    name=section_name,
                    grade_level=grade,
                    school_year=school_year,
                    defaults={'max_students': max_students}
                )
                if not created:
                    section.max_students = max_students
                    section.save()
                created_sections.append(section)

        return created_sections

    def create_subjects(self, grade_levels):
        """Create subjects for each grade level"""
        # Subject templates by grade level
        subject_templates = {
            'Kinder': [
                {'code': '0101', 'name': 'Mathematics', 'units': 1.0},
                {'code': '0102', 'name': 'Science', 'units': 1.0},
                {'code': '0103', 'name': 'English', 'units': 1.0},
            ],
            'Preparatory': [
                {'code': '0201', 'name': 'Mathematics', 'units': 1.0},
                {'code': '0202', 'name': 'Science', 'units': 1.0},
                {'code': '0203', 'name': 'English', 'units': 1.0},
            ],
            'Grade 1': [
                {'code': '0301', 'name': 'Mathematics', 'units': 1.0},
                {'code': '0302', 'name': 'English', 'units': 1.0},
                {'code': '0303', 'name': 'Filipino', 'units': 1.0},
            ],
            'Grade 2': [
                {'code': '0401', 'name': 'Mathematics', 'units': 1.0},
                {'code': '0402', 'name': 'English', 'units': 1.0},
                {'code': '0403', 'name': 'Filipino', 'units': 1.0},
            ],
            'Grade 3': [
                {'code': '0501', 'name': 'Mathematics', 'units': 1.0},
                {'code': '0502', 'name': 'English', 'units': 1.0},
                {'code': '0503', 'name': 'Filipino', 'units': 1.0},
            ],
            'Grade 4': [
                {'code': '0601', 'name': 'Mathematics', 'units': 1.0},
                {'code': '0602', 'name': 'English', 'units': 1.0},
                {'code': '0603', 'name': 'Science', 'units': 1.0},
            ],
            'Grade 5': [
                {'code': '0701', 'name': 'Mathematics', 'units': 1.0},
                {'code': '0702', 'name': 'English', 'units': 1.0},
                {'code': '0703', 'name': 'Science', 'units': 1.0},
            ],
            'Grade 6': [
                {'code': '0801', 'name': 'Mathematics', 'units': 1.0},
                {'code': '0802', 'name': 'English', 'units': 1.0},
                {'code': '0803', 'name': 'Science', 'units': 1.0},
            ],
        }

        created_subjects = []
        
        for grade in grade_levels:
            subjects_for_grade = subject_templates.get(grade.name, [])
            
            for subject_data in subjects_for_grade:
                subject, created = Subject.objects.get_or_create(
                    code=subject_data['code'],
                    grade_level=grade,
                    defaults={
                        'name': subject_data['name'],
                        'units': subject_data['units'],
                    }
                )
                created_subjects.append(subject)

        return created_subjects

    def create_schedules(self, school_year, sections, subjects):
        """Create class schedules for sections"""
        created_schedules = []
        
        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']
        time_slots = [
            ('08:00:00', '09:00:00'),
            ('09:00:00', '10:00:00'),
            ('10:15:00', '11:15:00'),
            ('11:15:00', '12:15:00'),
            ('13:00:00', '14:00:00'),
            ('14:00:00', '15:00:00'),
            ('15:15:00', '16:15:00'),
        ]
        
        # Create schedules for each section
        for section in sections:
            # Get subjects for this grade level
            grade_subjects = Subject.objects.filter(grade_level=section.grade_level)[:5]
            
            for idx, subject in enumerate(grade_subjects):
                day = days[idx % len(days)]
                time_start, time_end = time_slots[idx % len(time_slots)]
                room = f"Room {section.grade_level.level_order}{section.name}"
                
                schedule, created = ClassSchedule.objects.get_or_create(
                    subject=subject,
                    section=section,
                    school_year=school_year,
                    defaults={
                        'day': day,
                        'time_start': time_start,
                        'time_end': time_end,
                        'room': room,
                        'teacher': None,
                    }
                )
                created_schedules.append(schedule)

        return created_schedules
