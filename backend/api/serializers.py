"""
Serializers for API models.
"""

from rest_framework import serializers
from core.models import User, Course, Assignment, Submission, Feedback, PlagiarismReport, ExportJob


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model.
    """
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'student_id', 'is_active', 'date_joined'
        ]
        read_only_fields = ['id', 'date_joined']
        extra_kwargs = {
            'password': {'write_only': True}
        }
    
    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = User.objects.create(**validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user


class CourseSerializer(serializers.ModelSerializer):
    """
    Serializer for Course model.
    """
    instructor_name = serializers.CharField(source='instructor.get_full_name', read_only=True)
    student_count = serializers.SerializerMethodField()
    assignment_count = serializers.SerializerMethodField()
    students_list = serializers.SerializerMethodField()
    
    class Meta:
        model = Course
        fields = [
            'id', 'name', 'code', 'description', 'instructor', 'instructor_name',
            'students', 'students_list', 'is_active', 'created_at', 'updated_at',
            'student_count', 'assignment_count'
        ]
        read_only_fields = ['id', 'instructor', 'created_at', 'updated_at']
    
    def get_student_count(self, obj):
        return obj.get_student_count()
    
    def get_assignment_count(self, obj):
        return obj.get_assignment_count()
    
    def get_students_list(self, obj):
        return [
            {
                'id': str(student.id),
                'username': student.username,
                'name': student.get_full_name(),
                'student_id': student.student_id
            }
            for student in obj.students.all()
        ]


class AssignmentSerializer(serializers.ModelSerializer):
    """
    Serializer for Assignment model.
    """
    instructor_name = serializers.CharField(source='instructor.get_full_name', read_only=True)
    course_name = serializers.SerializerMethodField()
    course_code = serializers.SerializerMethodField()
    submission_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Assignment
        fields = [
            'id', 'title', 'description', 'course', 'course_name', 'course_code',
            'instructor', 'instructor_name', 'due_date', 'max_submissions',
            'created_at', 'updated_at', 'submission_count'
        ]
        read_only_fields = ['id', 'instructor', 'created_at', 'updated_at']
        extra_kwargs = {
            'course': {'required': False, 'allow_null': True}
        }
    
    def get_course_name(self, obj):
        try:
            if obj and hasattr(obj, 'course') and obj.course:
                return obj.course.name
            return None
        except (AttributeError, Exception):
            return None
    
    def get_course_code(self, obj):
        try:
            if obj and hasattr(obj, 'course') and obj.course:
                return obj.course.code
            return None
        except (AttributeError, Exception):
            return None
    
    def get_submission_count(self, obj):
        return obj.submissions.count()
    
    def validate_course(self, value):
        """Convert empty string to None for course field."""
        # Handle None, empty string, or empty UUID
        if value is None or value == '':
            return None
        # If it's a string, check if it's empty after stripping
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped or stripped == 'null' or stripped == 'None':
                return None
        return value


class SubmissionSerializer(serializers.ModelSerializer):
    """
    Serializer for Submission model.
    """
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    assignment_title = serializers.CharField(source='assignment.title', read_only=True)
    feedback_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Submission
        fields = [
            'id', 'assignment', 'assignment_title', 'student', 'student_name',
            'attempt_number', 'filename', 'file_type', 'status', 'submitted_at',
            'analyzed_at', 'feedback_approved_at', 'feedback_count'
        ]
        read_only_fields = [
            'id', 'student', 'submitted_at', 'analyzed_at', 'feedback_approved_at'
        ]
    
    def get_feedback_count(self, obj):
        return obj.feedback_items.count()


class FeedbackSerializer(serializers.ModelSerializer):
    """
    Serializer for Feedback model.
    """
    submission_title = serializers.CharField(source='submission.assignment.title', read_only=True)
    student_name = serializers.CharField(source='submission.student.get_full_name', read_only=True)
    reviewed_by_name = serializers.CharField(source='reviewed_by.get_full_name', read_only=True)
    assignment_id = serializers.UUIDField(source='submission.assignment.id', read_only=True)
    
    class Meta:
        model = Feedback
        fields = [
            'id', 'submission', 'submission_title', 'student_name', 'assignment_id',
            'line_number', 'severity', 'category', 'message', 'status',
            'created_at', 'reviewed_at', 'reviewed_by', 'reviewed_by_name',
            'instructor_notes'
        ]
        read_only_fields = [
            'id', 'created_at', 'reviewed_at', 'reviewed_by'
        ]


class PlagiarismReportSerializer(serializers.ModelSerializer):
    """
    Serializer for PlagiarismReport model.
    """
    submission1_student = serializers.CharField(source='submission1.student.get_full_name', read_only=True)
    submission2_student = serializers.CharField(source='submission2.student.get_full_name', read_only=True)
    assignment_title = serializers.CharField(source='submission1.assignment.title', read_only=True)
    reviewed_by_name = serializers.CharField(source='reviewed_by.get_full_name', read_only=True)
    
    class Meta:
        model = PlagiarismReport
        fields = [
            'id', 'submission1', 'submission2', 'submission1_student',
            'submission2_student', 'assignment_title', 'similarity_score',
            'matched_lines', 'status', 'created_at', 'reviewed_at',
            'reviewed_by', 'reviewed_by_name', 'instructor_notes'
        ]
        read_only_fields = [
            'id', 'created_at', 'reviewed_at', 'reviewed_by'
        ]


class ExportJobSerializer(serializers.ModelSerializer):
    """
    Serializer for ExportJob model.
    """
    
    class Meta:
        model = ExportJob
        fields = [
            'id', 'user', 'export_type', 'status', 'file_path',
            'parameters', 'created_at', 'completed_at', 'error_message'
        ]
        read_only_fields = [
            'id', 'user', 'created_at', 'completed_at'
        ]
