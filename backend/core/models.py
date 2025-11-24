"""
Core models for the code review system.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.conf import settings
import uuid
import os


class User(AbstractUser):
    """
    Extended user model with role-based access control.
    """
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('instructor', 'Instructor'),
        ('admin', 'Administrator'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    student_id = models.CharField(max_length=20, blank=True, null=True, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Fix reverse accessor conflicts
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name="custom_user_set",
        related_query_name="custom_user",
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name="custom_user_set",
        related_query_name="custom_user",
    )
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    def is_student(self):
        return self.role == 'student'
    
    def is_instructor(self):
        return self.role == 'instructor'
    
    def is_admin(self):
        return self.role == 'admin'


class Course(models.Model):
    """
    Represents a course/class that groups students and assignments.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, unique=True)  # e.g., "CPT_S 322"
    description = models.TextField(blank=True)
    instructor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='taught_courses')
    students = models.ManyToManyField(User, related_name='enrolled_courses', blank=True, limit_choices_to={'role': 'student'})
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    def get_student_count(self):
        return self.students.count()
    
    def get_assignment_count(self):
        return self.assignments.count()


class Assignment(models.Model):
    """
    Represents a coding assignment given to students.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='assignments', null=True, blank=True)
    instructor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assignments')
    due_date = models.DateTimeField(null=True, blank=True)
    max_submissions = models.IntegerField(default=3)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title


class Submission(models.Model):
    """
    Represents a student's code submission for an assignment.
    """
    STATUS_CHOICES = [
        ('submitted', 'Submitted'),
        ('analyzing', 'Analyzing'),
        ('pending_review', 'Pending Instructor Review'),
        ('feedback_ready', 'Feedback Ready'),
        ('resubmitted', 'Resubmitted'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submissions')
    attempt_number = models.IntegerField(default=1)
    filename = models.CharField(max_length=255)
    file = models.FileField(upload_to='submissions/%Y/%m/%d/', max_length=500, blank=True, null=True)
    file_content = models.TextField(blank=True, null=True)  # Kept for backward compatibility
    file_type = models.CharField(max_length=10)  # py, java, cpp
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='submitted')
    submitted_at = models.DateTimeField(auto_now_add=True)
    analyzed_at = models.DateTimeField(null=True, blank=True)
    feedback_approved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-submitted_at']
        unique_together = ['assignment', 'student', 'attempt_number']
    
    def __str__(self):
        return f"{self.student.username} - {self.assignment.title} (Attempt {self.attempt_number})"
    
    def get_file_content(self):
        """
        Get file content from file system or database (for backward compatibility).
        """
        # Try to read from file first
        if self.file and os.path.exists(self.file.path):
            try:
                with open(self.file.path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                print(f"Error reading file {self.file.path}: {str(e)}")
        
        # Fallback to database content (for old submissions)
        if self.file_content:
            return self.file_content
        
        return ""
    
    def save_file_content(self, content):
        """
        Save file content to disk and update the file field.
        """
        if not self.id:
            # Save model first to get ID
            super().save()
        
        # Create directory structure
        upload_dir = os.path.join(settings.MEDIA_ROOT, 'submissions', 
                                 str(self.submitted_at.year) if self.submitted_at else 'temp',
                                 str(self.submitted_at.month) if self.submitted_at else 'temp',
                                 str(self.submitted_at.day) if self.submitted_at else 'temp')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate file path
        file_extension = self.file_type or 'txt'
        file_path = os.path.join(upload_dir, f"{self.id}_{self.filename}")
        
        # Write content to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Update file field (relative to MEDIA_ROOT)
        relative_path = os.path.relpath(file_path, settings.MEDIA_ROOT)
        self.file.name = relative_path.replace('\\', '/')  # Use forward slashes for URLs
        
        # Optionally keep content in DB for quick access (can be removed later)
        # self.file_content = content
        
        self.save()
    
    def delete(self, *args, **kwargs):
        """
        Delete the file from disk when submission is deleted.
        """
        if self.file:
            if os.path.exists(self.file.path):
                try:
                    os.remove(self.file.path)
                except Exception as e:
                    print(f"Error deleting file {self.file.path}: {str(e)}")
        super().delete(*args, **kwargs)


class Feedback(models.Model):
    """
    Represents individual feedback items generated by AI analysis.
    """
    SEVERITY_CHOICES = [
        ('critical', 'Critical'),
        ('warning', 'Warning'),
        ('suggestion', 'Suggestion'),
    ]
    
    CATEGORY_CHOICES = [
        ('syntax', 'Syntax'),
        ('logic', 'Logic'),
        ('style', 'Style'),
        ('performance', 'Performance'),
        ('security', 'Security'),
        ('best_practice', 'Best Practice'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('edited', 'Edited'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name='feedback_items')
    line_number = models.IntegerField()
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_feedback')
    instructor_notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['line_number', 'created_at']
    
    def __str__(self):
        return f"Line {self.line_number}: {self.message[:50]}..."


class PlagiarismReport(models.Model):
    """
    Represents plagiarism detection results for submissions.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    submission1 = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name='plagiarism_as_sub1')
    submission2 = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name='plagiarism_as_sub2')
    similarity_score = models.FloatField()
    matched_lines = models.JSONField(default=list)
    status = models.CharField(max_length=20, choices=[
        ('flagged', 'Flagged'),
        ('reviewed', 'Reviewed'),
        ('dismissed', 'Dismissed'),
    ], default='flagged')
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    instructor_notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-similarity_score', '-created_at']
        unique_together = ['submission1', 'submission2']
    
    def __str__(self):
        return f"Plagiarism: {self.submission1.student.username} vs {self.submission2.student.username} ({self.similarity_score:.1%})"


class ExportJob(models.Model):
    """
    Represents export jobs for reports and data.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    EXPORT_TYPE_CHOICES = [
        ('pdf', 'PDF Report'),
        ('csv', 'CSV Data'),
        ('zip', 'ZIP Archive'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='export_jobs')
    export_type = models.CharField(max_length=10, choices=EXPORT_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    file_path = models.CharField(max_length=500, blank=True)
    parameters = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_export_type_display()} - {self.get_status_display()}"
