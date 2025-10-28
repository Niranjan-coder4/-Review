"""
Service classes for code analysis, plagiarism detection, and exports.
"""

import os
import json
import requests
import hashlib
from datetime import datetime
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from core.models import Submission, Feedback, PlagiarismReport


class CodeAnalysisService:
    """
    Service for analyzing code using AI/LLM.
    """
    
    def __init__(self):
        self.ai_api_key = settings.AI_API_KEY
        self.ai_api_url = settings.AI_API_URL
    
    def analyze_code(self, code_content, file_extension):
        """
        Analyze code and return feedback.
        """
        try:
            if not self.ai_api_key:
                return self._generate_mock_feedback(code_content, file_extension)
            
            return self._call_ai_api(code_content, file_extension)
        except Exception as e:
            return self._generate_mock_feedback(code_content, file_extension)
    
    def _call_ai_api(self, code_content, file_extension):
        """
        Call external AI API for code analysis.
        """
        language_map = {
            'py': 'Python',
            'java': 'Java',
            'cpp': 'C++'
        }
        language = language_map.get(file_extension, 'code')
        
        prompt = f"""Review this {language} code and provide feedback in JSON format.
        Return an array of feedback objects with these fields:
        - "line": line number (int)
        - "severity": "critical", "warning", or "suggestion"
        - "message": feedback text (string)
        - "category": "style", "logic", "performance", or "best_practice"
        
        Focus on:
        - Code style and formatting
        - Potential bugs or logic issues
        - Performance improvements
        - Best practices for {language}
        
        Code to review:
        ```{file_extension}
        {code_content}
        ```
        
        Return only valid JSON array, no other text."""
        
        headers = {
            'Authorization': f'Bearer {self.ai_api_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': 'gpt-3.5-turbo',
            'messages': [
                {'role': 'user', 'content': prompt}
            ],
            'temperature': 0.3,
            'max_tokens': 2000
        }
        
        response = requests.post(self.ai_api_url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        
        ai_response = response.json()
        content = ai_response['choices'][0]['message']['content'].strip()
        
        try:
            feedback = json.loads(content)
            return {'success': True, 'feedback': feedback}
        except json.JSONDecodeError:
            return self._generate_mock_feedback(code_content, file_extension)
    
    def _generate_mock_feedback(self, code_content, file_extension):
        """
        Generate mock feedback when AI is not available.
        """
        lines = code_content.split('\n')
        feedback = []
        
        for i, line in enumerate(lines, 1):
            line_lower = line.lower().strip()
            
            if file_extension == 'py':
                if 'print(' in line and 'f"' not in line and 'f\'' not in line and '%' not in line:
                    feedback.append({
                        "line": i,
                        "severity": "suggestion",
                        "message": "Consider using f-strings for better readability",
                        "category": "style"
                    })
                if '==' in line and 'is' in line:
                    feedback.append({
                        "line": i,
                        "severity": "warning",
                        "message": "Use '==' for value comparison, 'is' for identity comparison",
                        "category": "logic"
                    })
                if 'import *' in line:
                    feedback.append({
                        "line": i,
                        "severity": "warning",
                        "message": "Avoid 'import *' - it pollutes the namespace",
                        "category": "best_practice"
                    })
            
            elif file_extension == 'java':
                if 'System.out.println' in line:
                    feedback.append({
                        "line": i,
                        "severity": "suggestion",
                        "message": "Consider using a proper logging framework instead of System.out.println",
                        "category": "best_practice"
                    })
                if 'public static void main' in line and 'String[] args' not in line:
                    feedback.append({
                        "line": i,
                        "severity": "warning",
                        "message": "Main method should have String[] args parameter",
                        "category": "logic"
                    })
            
            elif file_extension == 'cpp':
                if 'using namespace std;' in line:
                    feedback.append({
                        "line": i,
                        "severity": "warning",
                        "message": "Avoid 'using namespace std' in header files",
                        "category": "best_practice"
                    })
                if 'cout' in line and 'endl' in line:
                    feedback.append({
                        "line": i,
                        "severity": "suggestion",
                        "message": "Consider using '\\n' instead of 'endl' for better performance",
                        "category": "performance"
                    })
        
        if not feedback:
            feedback.append({
                "line": 1,
                "severity": "suggestion",
                "message": "Code looks good! Consider adding comments for complex logic.",
                "category": "best_practice"
            })
        
        return {'success': True, 'feedback': feedback}


class PlagiarismDetectionService:
    """
    Service for detecting plagiarism in code submissions.
    """
    
    def check_submission(self, submission):
        """
        Check a submission for plagiarism against other submissions.
        """
        try:
            # Get other submissions for the same assignment
            other_submissions = Submission.objects.filter(
                assignment=submission.assignment
            ).exclude(id=submission.id)
            
            for other_submission in other_submissions:
                similarity_score = self._calculate_similarity(
                    submission.file_content,
                    other_submission.file_content
                )
                
                if similarity_score > 0.9:  # 90% threshold
                    self._create_plagiarism_report(submission, other_submission, similarity_score)
        
        except Exception as e:
            print(f"Plagiarism check error: {str(e)}")
    
    def _calculate_similarity(self, code1, code2):
        """
        Calculate similarity between two code files.
        """
        # Simple token-based similarity
        tokens1 = set(code1.split())
        tokens2 = set(code2.split())
        
        if not tokens1 and not tokens2:
            return 1.0
        if not tokens1 or not tokens2:
            return 0.0
        
        intersection = len(tokens1.intersection(tokens2))
        union = len(tokens1.union(tokens2))
        
        return intersection / union if union > 0 else 0.0
    
    def _create_plagiarism_report(self, submission1, submission2, similarity_score):
        """
        Create a plagiarism report for two submissions.
        """
        try:
            PlagiarismReport.objects.get_or_create(
                submission1=submission1,
                submission2=submission2,
                defaults={
                    'similarity_score': similarity_score,
                    'matched_lines': [],  # Could be enhanced to show specific matches
                    'status': 'flagged'
                }
            )
        except Exception as e:
            print(f"Error creating plagiarism report: {str(e)}")


class ExportService:
    """
    Service for exporting reports and data.
    """
    
    def export_pdf_report(self, submission, user):
        """
        Export a PDF report for a submission.
        """
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib.units import inch
            
            # Create PDF
            filename = f"submission_report_{submission.id}.pdf"
            filepath = os.path.join(settings.MEDIA_ROOT, 'exports', filename)
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            doc = SimpleDocTemplate(filepath, pagesize=letter)
            styles = getSampleStyleSheet()
            story = []
            
            # Title
            title = Paragraph(f"Code Review Report: {submission.assignment.title}", styles['Title'])
            story.append(title)
            story.append(Spacer(1, 12))
            
            # Student info
            student_info = Paragraph(f"Student: {submission.student.get_full_name()}", styles['Normal'])
            story.append(student_info)
            story.append(Spacer(1, 12))
            
            # Feedback items
            feedback_items = submission.feedback_items.filter(status='approved')
            for feedback in feedback_items:
                feedback_text = f"Line {feedback.line_number} ({feedback.severity}): {feedback.message}"
                story.append(Paragraph(feedback_text, styles['Normal']))
                story.append(Spacer(1, 6))
            
            doc.build(story)
            
            return filepath
            
        except Exception as e:
            raise Exception(f"PDF export failed: {str(e)}")
    
    def export_csv_data(self, assignment, user):
        """
        Export CSV data for an assignment.
        """
        try:
            import csv
            
            filename = f"assignment_data_{assignment.id}.csv"
            filepath = os.path.join(settings.MEDIA_ROOT, 'exports', filename)
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Header
                writer.writerow([
                    'Student ID', 'Student Name', 'Submission Date', 'Status',
                    'Feedback Count', 'Critical Issues', 'Warnings', 'Suggestions'
                ])
                
                # Data
                submissions = assignment.submissions.all()
                for submission in submissions:
                    feedback_items = submission.feedback_items.filter(status='approved')
                    critical_count = feedback_items.filter(severity='critical').count()
                    warning_count = feedback_items.filter(severity='warning').count()
                    suggestion_count = feedback_items.filter(severity='suggestion').count()
                    
                    writer.writerow([
                        submission.student.student_id or '',
                        submission.student.get_full_name(),
                        submission.submitted_at.strftime('%Y-%m-%d %H:%M'),
                        submission.status,
                        feedback_items.count(),
                        critical_count,
                        warning_count,
                        suggestion_count
                    ])
            
            return filepath
            
        except Exception as e:
            raise Exception(f"CSV export failed: {str(e)}")
