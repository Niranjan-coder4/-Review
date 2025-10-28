"""
Core app admin configuration.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Assignment, Submission, Feedback, PlagiarismReport, ExportJob


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'student_id', 'is_active', 'date_joined')
    list_filter = ('role', 'is_active', 'is_staff', 'date_joined')
    search_fields = ('username', 'email', 'student_id')
    ordering = ('username',)
    
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('role', 'student_id')}),
    )


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'instructor', 'due_date', 'created_at')
    list_filter = ('instructor', 'created_at')
    search_fields = ('title', 'description')
    ordering = ('-created_at',)


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('student', 'assignment', 'attempt_number', 'status', 'submitted_at')
    list_filter = ('status', 'assignment', 'submitted_at')
    search_fields = ('student__username', 'assignment__title', 'filename')
    ordering = ('-submitted_at',)


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('submission', 'line_number', 'severity', 'category', 'status')
    list_filter = ('severity', 'category', 'status', 'created_at')
    search_fields = ('submission__student__username', 'message')
    ordering = ('-created_at',)


@admin.register(PlagiarismReport)
class PlagiarismReportAdmin(admin.ModelAdmin):
    list_display = ('submission1', 'submission2', 'similarity_score', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('submission1__student__username', 'submission2__student__username')
    ordering = ('-similarity_score',)


@admin.register(ExportJob)
class ExportJobAdmin(admin.ModelAdmin):
    list_display = ('user', 'export_type', 'status', 'created_at')
    list_filter = ('export_type', 'status', 'created_at')
    search_fields = ('user__username',)
    ordering = ('-created_at',)
