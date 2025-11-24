"""
Management command to create sample data for testing.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import Assignment, Submission, Feedback, PlagiarismReport

User = get_user_model()


class Command(BaseCommand):
    help = 'Create sample data for testing the code review system'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample data...')
        
        # Create sample users
        instructor, created = User.objects.get_or_create(
            username='instructor1',
            defaults={
                'email': 'instructor@example.com',
                'first_name': 'Dr. Jane',
                'last_name': 'Smith',
                'role': 'instructor'
            }
        )
        if created:
            instructor.set_password('password123')
            instructor.save()
            self.stdout.write(f'Created instructor: {instructor.username}')
        
        student1, created = User.objects.get_or_create(
            username='student1',
            defaults={
                'email': 'student1@example.com',
                'first_name': 'John',
                'last_name': 'William',
                'role': 'student',
                'student_id': '12345'
            }
        )
        if created:
            student1.set_password('password123')
            student1.save()
            self.stdout.write(f'Created student: {student1.username}')
        
        student2, created = User.objects.get_or_create(
            username='student2',
            defaults={
                'email': 'student2@example.com',
                'first_name': 'Alice',
                'last_name': 'Johnson',
                'role': 'student',
                'student_id': '67890'
            }
        )
        if created:
            student2.set_password('password123')
            student2.save()
            self.stdout.write(f'Created student: {student2.username}')
        
        # Create sample assignment
        assignment, created = Assignment.objects.get_or_create(
            title='Python Basics Assignment',
            defaults={
                'description': 'Write a Python program that demonstrates basic programming concepts.',
                'instructor': instructor,
                'max_submissions': 3
            }
        )
        if created:
            self.stdout.write(f'Created assignment: {assignment.title}')
        
        # Create sample submissions
        sample_code1 = '''def calculate_factorial(n):
    if n == 0:
        return 1
    else:
        return n * calculate_factorial(n-1)

print("Factorial of 5 is:", calculate_factorial(5))'''

        sample_code2 = '''def calculate_factorial(n):
    if n == 0:
        return 1
    else:
        return n * calculate_factorial(n-1)

print("Factorial of 5 is:", calculate_factorial(5))'''

        submission1, created = Submission.objects.get_or_create(
            assignment=assignment,
            student=student1,
            attempt_number=1,
            defaults={
                'filename': 'factorial.py',
                'file_type': 'py',
                'status': 'feedback_ready'
            }
        )
        if created:
            submission1.save_file_content(sample_code1)
            self.stdout.write(f'Created submission: {submission1.filename}')
        
        submission2, created = Submission.objects.get_or_create(
            assignment=assignment,
            student=student2,
            attempt_number=1,
            defaults={
                'filename': 'factorial.py',
                'file_type': 'py',
                'status': 'feedback_ready'
            }
        )
        if created:
            submission2.save_file_content(sample_code2)
            self.stdout.write(f'Created submission: {submission2.filename}')
        
        # Create sample feedback
        if submission1:
            feedback1, created = Feedback.objects.get_or_create(
                submission=submission1,
                line_number=1,
                defaults={
                    'severity': 'suggestion',
                    'category': 'style',
                    'message': 'Consider adding a docstring to explain what this function does.',
                    'status': 'approved'
                }
            )
            if created:
                self.stdout.write(f'Created feedback for submission 1')
        
        if submission2:
            feedback2, created = Feedback.objects.get_or_create(
                submission=submission2,
                line_number=1,
                defaults={
                    'severity': 'suggestion',
                    'category': 'style',
                    'message': 'Consider adding a docstring to explain what this function does.',
                    'status': 'pending'
                }
            )
            if created:
                self.stdout.write(f'Created feedback for submission 2')
        
        # Create sample plagiarism report
        if submission1 and submission2:
            plagiarism_report, created = PlagiarismReport.objects.get_or_create(
                submission1=submission1,
                submission2=submission2,
                defaults={
                    'similarity_score': 0.95,
                    'matched_lines': [1, 2, 3, 4, 5, 6],
                    'status': 'flagged'
                }
            )
            if created:
                self.stdout.write(f'Created plagiarism report')
        
        self.stdout.write(
            self.style.SUCCESS('Sample data created successfully!')
        )
        self.stdout.write('You can now login with:')
        self.stdout.write('  Instructor: instructor1 / password123')
        self.stdout.write('  Student 1: student1 / password123')
        self.stdout.write('  Student 2: student2 / password123')
