"""
API views for the code review system.
"""

import os
import json
import requests
import hashlib
from datetime import datetime
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import authenticate, login, logout
from core.models import User, Course, Assignment, Submission, Feedback, PlagiarismReport, ExportJob
from .serializers import (
    UserSerializer, CourseSerializer, AssignmentSerializer, SubmissionSerializer, FeedbackSerializer,
    PlagiarismReportSerializer, ExportJobSerializer
)
from .services import CodeAnalysisService, PlagiarismDetectionService, ExportService


class CourseViewSet(viewsets.ModelViewSet):
    """
    ViewSet for course management.
    """
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_instructor() or user.is_admin():
            return Course.objects.filter(instructor=user)
        elif user.is_student():
            return Course.objects.filter(students=user, is_active=True)
        return Course.objects.none()
    
    def perform_create(self, serializer):
        serializer.save(instructor=self.request.user)
    
    @action(detail=True, methods=['post'])
    def add_student(self, request, pk=None):
        """
        Add a student to the course.
        """
        course = self.get_object()
        if not request.user.is_instructor() and not request.user.is_admin():
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        student_id = request.data.get('student_id')
        if not student_id:
            return Response({'error': 'Student ID required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            student = User.objects.get(id=student_id, role='student')
            course.students.add(student)
            return Response({'success': True, 'message': f'Student {student.username} added to course'})
        except User.DoesNotExist:
            return Response({'error': 'Student not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'])
    def remove_student(self, request, pk=None):
        """
        Remove a student from the course.
        """
        course = self.get_object()
        if not request.user.is_instructor() and not request.user.is_admin():
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        student_id = request.data.get('student_id')
        if not student_id:
            return Response({'error': 'Student ID required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            student = User.objects.get(id=student_id, role='student')
            course.students.remove(student)
            return Response({'success': True, 'message': f'Student {student.username} removed from course'})
        except User.DoesNotExist:
            return Response({'error': 'Student not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['get'])
    def students(self, request, pk=None):
        """
        Get all students in the course.
        """
        course = self.get_object()
        students = course.students.all()
        serializer = UserSerializer(students, many=True)
        return Response(serializer.data)


class AssignmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for assignment management.
    """
    queryset = Assignment.objects.all()
    serializer_class = AssignmentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        course_id = self.request.query_params.get('course_id', None)
        
        if user.is_instructor() or user.is_admin():
            queryset = Assignment.objects.filter(instructor=user)
            if course_id:
                queryset = queryset.filter(course_id=course_id)
            return queryset
        elif user.is_student():
            # Students see assignments from courses they're enrolled in
            queryset = Assignment.objects.filter(course__students=user, course__is_active=True)
            if course_id:
                queryset = queryset.filter(course_id=course_id)
            return queryset
        return Assignment.objects.none()
    
    def perform_create(self, serializer):
        serializer.save(instructor=self.request.user)
    
    @action(detail=True, methods=['get'])
    def submissions(self, request, pk=None):
        """
        Get all submissions for an assignment.
        """
        assignment = self.get_object()
        submissions = Submission.objects.filter(assignment=assignment)
        
        if request.user.is_student():
            submissions = submissions.filter(student=request.user)
        
        serializer = SubmissionSerializer(submissions, many=True)
        return Response(serializer.data)


class SubmissionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for submission management.
    """
    queryset = Submission.objects.all()
    serializer_class = SubmissionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_instructor() or user.is_admin():
            return Submission.objects.all()
        elif user.is_student():
            return Submission.objects.filter(student=user)
        return Submission.objects.none()
    
    def perform_create(self, serializer):
        serializer.save(student=self.request.user)
    
    @action(detail=True, methods=['get'])
    def feedback(self, request, pk=None):
        """
        Get feedback for a submission.
        """
        submission = self.get_object()
        
        # Only show approved feedback to students
        if request.user.is_student():
            feedback = submission.feedback_items.filter(status='approved')
        else:
            feedback = submission.feedback_items.all()
        
        serializer = FeedbackSerializer(feedback, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def code(self, request, pk=None):
        """
        Get code content with feedback annotations.
        """
        submission = self.get_object()
        
        # Check permissions
        if request.user.is_student() and submission.student != request.user:
            return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
        
        # Get feedback
        if request.user.is_student():
            feedback = submission.feedback_items.filter(status='approved')
        else:
            feedback = submission.feedback_items.all()
        
        # Get file content from file system
        file_content = submission.get_file_content()
        if not file_content:
            return Response({'error': 'File content not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Format code with line numbers
        lines = file_content.split('\n')
        code_with_feedback = []
        
        for i, line in enumerate(lines, 1):
            line_feedback = [f for f in feedback if f.line_number == i]
            code_with_feedback.append({
                'line_number': i,
                'content': line,
                'feedback': [
                    {
                        'id': str(f.id),
                        'severity': f.severity,
                        'category': f.category,
                        'message': f.message,
                        'status': f.status,
                        'instructor_notes': f.instructor_notes
                    } for f in line_feedback
                ]
            })
        
        return Response({
            'submission_id': str(submission.id),
            'filename': submission.filename,
            'file_type': submission.file_type,
            'code': code_with_feedback,
            'total_lines': len(lines)
        })
    
    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        """
        Get submission history for a student.
        """
        submission = self.get_object()
        if request.user.is_student() and submission.student != request.user:
            return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
        
        # Get all submissions for the same assignment by the same student
        history = Submission.objects.filter(
            assignment=submission.assignment,
            student=submission.student
        ).order_by('attempt_number')
        
        serializer = SubmissionSerializer(history, many=True)
        return Response(serializer.data)


class FeedbackViewSet(viewsets.ModelViewSet):
    """
    ViewSet for feedback management.
    """
    queryset = Feedback.objects.all()
    serializer_class = FeedbackSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_instructor() or user.is_admin():
            return Feedback.objects.all()
        elif user.is_student():
            return Feedback.objects.filter(
                submission__student=user,
                status='approved'
            )
        return Feedback.objects.none()
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """
        Approve a feedback item.
        """
        feedback = self.get_object()
        if not request.user.is_instructor() and not request.user.is_admin():
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        feedback.status = 'approved'
        feedback.reviewed_at = timezone.now()
        feedback.reviewed_by = request.user
        feedback.save()
        
        return Response({'success': True, 'message': 'Feedback approved'})
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """
        Reject a feedback item.
        """
        feedback = self.get_object()
        if not request.user.is_instructor() and not request.user.is_admin():
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        feedback.status = 'rejected'
        feedback.reviewed_at = timezone.now()
        feedback.reviewed_by = request.user
        feedback.save()
        
        return Response({'success': True, 'message': 'Feedback rejected'})
    
    @action(detail=True, methods=['post'])
    def edit(self, request, pk=None):
        """
        Edit a feedback item.
        """
        feedback = self.get_object()
        if not request.user.is_instructor() and not request.user.is_admin():
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        message = request.data.get('message', feedback.message)
        instructor_notes = request.data.get('instructor_notes', '')
        
        feedback.message = message
        feedback.instructor_notes = instructor_notes
        feedback.status = 'edited'
        feedback.reviewed_at = timezone.now()
        feedback.reviewed_by = request.user
        feedback.save()
        
        return Response({'success': True, 'message': 'Feedback edited'})


class PlagiarismReportViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for plagiarism reports.
    """
    queryset = PlagiarismReport.objects.all()
    serializer_class = PlagiarismReportSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_instructor() or user.is_admin():
            return PlagiarismReport.objects.all()
        return PlagiarismReport.objects.none()
    
    @action(detail=True, methods=['post'])
    def dismiss(self, request, pk=None):
        """
        Dismiss a plagiarism report.
        """
        report = self.get_object()
        if not request.user.is_instructor() and not request.user.is_admin():
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        report.status = 'dismissed'
        report.reviewed_at = timezone.now()
        report.reviewed_by = request.user
        report.save()
        
        return Response({'success': True, 'message': 'Plagiarism report dismissed'})


class ExportJobViewSet(viewsets.ModelViewSet):
    """
    ViewSet for export jobs.
    """
    queryset = ExportJob.objects.all()
    serializer_class = ExportJobSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return ExportJob.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ExportView(APIView):
    """
    Handle export requests for PDF and CSV.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        export_type = request.data.get('export_type')  # 'pdf' or 'csv'
        submission_id = request.data.get('submission_id')
        assignment_id = request.data.get('assignment_id')
        
        if not export_type or export_type not in ['pdf', 'csv']:
            return Response({'error': 'Invalid export type'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            export_service = ExportService()
            
            if export_type == 'pdf':
                if not submission_id:
                    return Response({'error': 'Submission ID required for PDF export'}, 
                                  status=status.HTTP_400_BAD_REQUEST)
                
                submission = Submission.objects.get(id=submission_id)
                
                # Check permissions
                if request.user.is_student() and submission.student != request.user:
                    return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
                
                filepath = export_service.export_pdf_report(submission, request.user)
                
                # Return file for download
                from django.http import FileResponse
                import os
                return FileResponse(
                    open(filepath, 'rb'),
                    as_attachment=True,
                    filename=os.path.basename(filepath)
                )
            
            elif export_type == 'csv':
                if not assignment_id:
                    return Response({'error': 'Assignment ID required for CSV export'}, 
                                  status=status.HTTP_400_BAD_REQUEST)
                
                assignment = Assignment.objects.get(id=assignment_id)
                
                # Check permissions
                if request.user.is_student():
                    return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
                
                filepath = export_service.export_csv_data(assignment, request.user)
                
                # Return file for download
                from django.http import FileResponse
                import os
                return FileResponse(
                    open(filepath, 'rb'),
                    as_attachment=True,
                    filename=os.path.basename(filepath)
                )
        
        except Submission.DoesNotExist:
            return Response({'error': 'Submission not found'}, status=status.HTTP_404_NOT_FOUND)
        except Assignment.DoesNotExist:
            return Response({'error': 'Assignment not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': f'Export failed: {str(e)}'}, 
                          status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FileUploadView(APIView):
    """
    Handle file uploads for code analysis.
    Supports single files and ZIP archives.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        if 'file' not in request.files:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        file = request.files['file']
        assignment_id = request.data.get('assignment_id')
        
        if not assignment_id:
            return Response({'error': 'Assignment ID required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            assignment = Assignment.objects.get(id=assignment_id)
        except Assignment.DoesNotExist:
            return Response({'error': 'Assignment not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Check if it's a ZIP file
        if file.filename.lower().endswith('.zip'):
            return self._handle_zip_upload(file, assignment, request.user)
        
        # Handle single file upload
        return self._handle_single_upload(file, assignment, request.user)
    
    def _handle_single_upload(self, file, assignment, user):
        """Handle single file upload."""
        # Validate file type
        allowed_extensions = {'py', 'java', 'cpp'}
        file_extension = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        
        if file_extension not in allowed_extensions:
            return Response({
                'error': 'Please upload a supported code file (.py, .java, .cpp)'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check file size (16MB limit)
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Reset to beginning
        
        if file_size > 16 * 1024 * 1024:  # 16MB
            return Response({'error': 'File size exceeds 16MB limit'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Read file content
        try:
            file_content = file.read().decode('utf-8')
        except UnicodeDecodeError:
            return Response({'error': 'File encoding not supported. Please use UTF-8.'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Get next attempt number
        last_submission = Submission.objects.filter(
            assignment=assignment,
            student=user
        ).order_by('-attempt_number').first()
        
        attempt_number = (last_submission.attempt_number + 1) if last_submission else 1
        
        # Create submission
        with transaction.atomic():
            submission = Submission.objects.create(
                assignment=assignment,
                student=user,
                attempt_number=attempt_number,
                filename=file.filename,
                file_type=file_extension,
                status='analyzing'
            )
            
            # Save file to disk
            submission.save_file_content(file_content)
            
            try:
                # Start analysis (read from file)
                analysis_service = CodeAnalysisService()
                analysis_result = analysis_service.analyze_code(file_content, file_extension)
                
                if analysis_result['success']:
                    # Create feedback items
                    for feedback_data in analysis_result['feedback']:
                        Feedback.objects.create(
                            submission=submission,
                            line_number=feedback_data['line'],
                            severity=feedback_data['severity'],
                            category=feedback_data['category'],
                            message=feedback_data['message']
                        )
                    
                    submission.status = 'pending_review'
                    submission.analyzed_at = timezone.now()
                    submission.save()
                    
                    # Run plagiarism check asynchronously (in production, use Celery)
                    plagiarism_service = PlagiarismDetectionService()
                    plagiarism_service.check_submission(submission)
                    
                    return Response({
                        'success': True,
                        'message': 'File uploaded and analyzed successfully',
                        'submission_id': str(submission.id),
                        'feedback_count': len(analysis_result['feedback'])
                    })
                else:
                    submission.status = 'submitted'
                    submission.save()
                    return Response({
                        'success': False,
                        'error': analysis_result.get('error', 'Analysis failed')
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            except Exception as e:
                submission.status = 'submitted'
                submission.save()
                return Response({
                    'success': False,
                    'error': f'Analysis error: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _handle_zip_upload(self, file, assignment, user):
        """Handle ZIP file upload and extract multiple files."""
        import zipfile
        import io
        
        try:
            # Read ZIP file
            zip_data = file.read()
            zip_file = zipfile.ZipFile(io.BytesIO(zip_data))
            
            # Get list of files in ZIP
            file_list = zip_file.namelist()
            
            # Filter for supported code files
            allowed_extensions = {'.py', '.java', '.cpp'}
            code_files = [
                f for f in file_list 
                if any(f.lower().endswith(ext) for ext in allowed_extensions) 
                and not f.endswith('/')
            ]
            
            if not code_files:
                return Response({
                    'error': 'No supported code files found in ZIP archive'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Process each file
            results = []
            errors = []
            
            for code_file in code_files[:10]:  # Limit to 10 files
                try:
                    # Read file content
                    file_content = zip_file.read(code_file).decode('utf-8')
                    file_extension = code_file.rsplit('.', 1)[1].lower()
                    
                    # Get next attempt number
                    last_submission = Submission.objects.filter(
                        assignment=assignment,
                        student=user
                    ).order_by('-attempt_number').first()
                    
                    attempt_number = (last_submission.attempt_number + 1) if last_submission else 1
                    
                    # Create submission
                    submission = Submission.objects.create(
                        assignment=assignment,
                        student=user,
                        attempt_number=attempt_number,
                        filename=code_file,
                        file_type=file_extension,
                        status='analyzing'
                    )
                    
                    # Save file to disk
                    submission.save_file_content(file_content)
                    
                    # Analyze
                    analysis_service = CodeAnalysisService()
                    analysis_result = analysis_service.analyze_code(file_content, file_extension)
                    
                    if analysis_result['success']:
                        for feedback_data in analysis_result['feedback']:
                            Feedback.objects.create(
                                submission=submission,
                                line_number=feedback_data['line'],
                                severity=feedback_data['severity'],
                                category=feedback_data['category'],
                                message=feedback_data['message']
                            )
                        
                        submission.status = 'pending_review'
                        submission.analyzed_at = timezone.now()
                        submission.save()
                        
                        # Run plagiarism check
                        plagiarism_service = PlagiarismDetectionService()
                        plagiarism_service.check_submission(submission)
                        
                        results.append({
                            'filename': code_file,
                            'submission_id': str(submission.id),
                            'feedback_count': len(analysis_result['feedback'])
                        })
                    else:
                        errors.append(f'{code_file}: Analysis failed')
                
                except Exception as e:
                    errors.append(f'{code_file}: {str(e)}')
            
            return Response({
                'success': True,
                'message': f'Processed {len(results)} files from ZIP archive',
                'results': results,
                'errors': errors if errors else None
            })
        
        except zipfile.BadZipFile:
            return Response({'error': 'Invalid ZIP file'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': f'ZIP processing failed: {str(e)}'}, 
                          status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def get(self, request):
        return Response({'message': 'File upload endpoint'}, status=status.HTTP_200_OK)


class CodeAnalysisView(APIView):
    """
    Handle code analysis requests.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        code_content = request.data.get('code')
        file_type = request.data.get('file_type')
        
        if not code_content or not file_type:
            return Response({
                'error': 'Code content and file type required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        analysis_service = CodeAnalysisService()
        result = analysis_service.analyze_code(code_content, file_type)
        
        return Response(result)


class HealthCheckView(APIView):
    """
    Health check endpoint.
    """
    
    def get(self, request):
        return Response({
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'ai_configured': bool(settings.AI_API_KEY)
        })


# Authentication Views
class LoginView(APIView):
    """
    User login endpoint.
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not username or not password:
            return Response({'error': 'Username and password required'}, 
                           status=status.HTTP_400_BAD_REQUEST)
        
        user = authenticate(username=username, password=password)
        if user:
            login(request, user)
            serializer = UserSerializer(user)
            return Response({
                'user': serializer.data,
                'message': 'Login successful'
            })
        else:
            return Response({'error': 'Invalid credentials'}, 
                           status=status.HTTP_401_UNAUTHORIZED)


class LogoutView(APIView):
    """
    User logout endpoint.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        logout(request)
        return Response({'message': 'Logout successful'})


class RegisterView(APIView):
    """
    User registration endpoint.
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            user.set_password(request.data.get('password'))
            user.save()
            return Response({
                'user': UserSerializer(user).data,
                'message': 'Registration successful'
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CreateStudentView(APIView):
    """
    Endpoint for instructors to create students.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        if not request.user.is_instructor() and not request.user.is_admin():
            return Response({'error': 'Permission denied. Only instructors can create students.'}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        # Ensure role is set to student
        data = request.data.copy()
        data['role'] = 'student'
        
        serializer = UserSerializer(data=data)
        if serializer.is_valid():
            user = serializer.save()
            password = request.data.get('password', 'password123')  # Default password
            user.set_password(password)
            user.save()
            
            return Response({
                'user': UserSerializer(user).data,
                'message': f'Student {user.username} created successfully',
                'password': password  # Return password for instructor to share
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProfileView(APIView):
    """
    User profile endpoint.
    """
    permission_classes = [AllowAny]  # Allow any for session-based auth
    
    def get(self, request):
        if request.user.is_authenticated:
            serializer = UserSerializer(request.user)
            return Response(serializer.data)
        else:
            return Response({'error': 'Not authenticated'}, status=status.HTTP_401_UNAUTHORIZED)
    
    def put(self, request):
        if request.user.is_authenticated:
            serializer = UserSerializer(request.user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'error': 'Not authenticated'}, status=status.HTTP_401_UNAUTHORIZED)
