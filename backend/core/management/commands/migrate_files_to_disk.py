"""
Management command to migrate existing file_content from database to file system.
Run this after updating the model to migrate existing submissions.
"""

from django.core.management.base import BaseCommand
from core.models import Submission
import os
from django.conf import settings


class Command(BaseCommand):
    help = 'Migrate file content from database to file system'

    def handle(self, *args, **options):
        self.stdout.write('Starting file migration...')
        
        # Get all submissions with file_content but no file
        submissions = Submission.objects.filter(
            file_content__isnull=False
        ).exclude(file_content='')
        
        total = submissions.count()
        self.stdout.write(f'Found {total} submissions to migrate')
        
        migrated = 0
        errors = 0
        
        for submission in submissions:
            try:
                # Check if file already exists
                if submission.file and os.path.exists(submission.file.path):
                    self.stdout.write(f'Skipping {submission.id} - file already exists')
                    continue
                
                # Save file content to disk
                submission.save_file_content(submission.file_content)
                migrated += 1
                
                if migrated % 10 == 0:
                    self.stdout.write(f'Migrated {migrated}/{total} submissions...')
            
            except Exception as e:
                errors += 1
                self.stdout.write(
                    self.style.ERROR(f'Error migrating {submission.id}: {str(e)}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nMigration complete! Migrated: {migrated}, Errors: {errors}'
            )
        )

