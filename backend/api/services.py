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
        Supports both OpenAI format and Hugging Face inference API.
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
        
        # Detect API type
        is_huggingface = 'huggingface.co' in self.ai_api_url.lower() or 'hf.co' in self.ai_api_url.lower() or 'router.huggingface.co' in self.ai_api_url.lower()
        is_gemini = 'generativelanguage.googleapis.com' in self.ai_api_url.lower() or 'gemini' in self.ai_api_url.lower()
        
        # Update old Hugging Face URLs to new router endpoint
        if 'api-inference.huggingface.co' in self.ai_api_url:
            # Extract model name from old URL
            import re
            model_match = re.search(r'/models/([^/]+)', self.ai_api_url)
            if model_match:
                model_name = model_match.group(1)
                self.ai_api_url = f'https://router.huggingface.co/models/{model_name}'
                print(f"Updated Hugging Face URL to: {self.ai_api_url}")
        
        # Initialize request URL (will be modified for Gemini)
        request_url = self.ai_api_url
        headers = {}
        data = {}
        
        if is_gemini:
            # Google Gemini API format
            # API key goes in URL as query parameter, not header
            request_url = f"{self.ai_api_url}?key={self.ai_api_key}"
            headers = {
                'Content-Type': 'application/json'
            }
            data = {
                'contents': [{
                    'parts': [{
                        'text': prompt
                    }]
                }],
                'generationConfig': {
                    'temperature': 0.3,
                    'maxOutputTokens': 2000
                }
            }
        elif is_huggingface:
            # Hugging Face Inference API format
            headers = {
                'Authorization': f'Bearer {self.ai_api_key}',
                'Content-Type': 'application/json'
            }
            data = {
                'inputs': prompt,
                'parameters': {
                    'max_new_tokens': 2000,
                    'temperature': 0.3,
                    'return_full_text': False
                }
            }
        else:
            # OpenAI/OpenAI-compatible format
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
        
        try:
            # request_url is already set above (includes API key for Gemini)
            response = requests.post(request_url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            
            ai_response = response.json()
            
            # Parse Gemini response
            if is_gemini:
                if 'candidates' in ai_response and len(ai_response['candidates']) > 0:
                    candidate = ai_response['candidates'][0]
                    if 'content' in candidate and 'parts' in candidate['content']:
                        content = candidate['content']['parts'][0].get('text', '').strip()
                    else:
                        content = str(ai_response).strip()
                else:
                    content = str(ai_response).strip()
            # Parse Hugging Face response
            elif is_huggingface:
                if isinstance(ai_response, list) and len(ai_response) > 0:
                    if 'generated_text' in ai_response[0]:
                        content = ai_response[0]['generated_text'].strip()
                    else:
                        content = str(ai_response[0]).strip()
                elif isinstance(ai_response, dict) and 'generated_text' in ai_response:
                    content = ai_response['generated_text'].strip()
                else:
                    content = str(ai_response).strip()
            else:
                # OpenAI format
                content = ai_response['choices'][0]['message']['content'].strip()
            
            # Try to extract JSON from response
            try:
                # Look for JSON array in the response
                import re
                json_match = re.search(r'\[.*\]', content, re.DOTALL)
                if json_match:
                    content = json_match.group(0)
                
                feedback = json.loads(content)
                if isinstance(feedback, list) and len(feedback) > 0:
                    return {'success': True, 'feedback': feedback}
                else:
                    raise ValueError("Empty feedback array")
            except (json.JSONDecodeError, ValueError) as e:
                print(f"Failed to parse AI response as JSON: {str(e)}")
                print(f"Response content: {content[:500]}")
                # For Gemini, try to extract JSON from markdown code blocks
                if is_gemini:
                    json_in_code_block = re.search(r'```(?:json)?\s*(\[.*?\])\s*```', content, re.DOTALL)
                    if json_in_code_block:
                        try:
                            feedback = json.loads(json_in_code_block.group(1))
                            if isinstance(feedback, list) and len(feedback) > 0:
                                return {'success': True, 'feedback': feedback}
                        except:
                            pass
                return self._generate_mock_feedback(code_content, file_extension)
        
        except requests.exceptions.RequestException as e:
            print(f"AI API request failed: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    print(f"Error details: {error_detail}")
                except:
                    print(f"Error response: {e.response.text[:500]}")
            return self._generate_mock_feedback(code_content, file_extension)
        except Exception as e:
            print(f"Unexpected error calling AI API: {str(e)}")
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
                # Get file content from file system
                code1 = submission.get_file_content()
                code2 = other_submission.get_file_content()
                
                if not code1 or not code2:
                    continue
                
                similarity_score = self._calculate_similarity(code1, code2)
                
                if similarity_score > 0.9:  # 90% threshold
                    self._create_plagiarism_report(submission, other_submission, similarity_score)
        
        except Exception as e:
            print(f"Plagiarism check error: {str(e)}")
    
    def _calculate_similarity(self, code1, code2):
        """
        Calculate similarity between two code files using multiple algorithms.
        """
        if not code1 or not code2:
            return 0.0
        
        # Normalize code (remove comments, extra whitespace)
        code1_normalized = self._normalize_code(code1)
        code2_normalized = self._normalize_code(code2)
        
        if not code1_normalized or not code2_normalized:
            return 0.0
        
        # Method 1: Token-based Jaccard similarity
        tokens1 = set(code1_normalized.split())
        tokens2 = set(code2_normalized.split())
        
        if not tokens1 and not tokens2:
            return 1.0
        
        jaccard = len(tokens1.intersection(tokens2)) / len(tokens1.union(tokens2)) if tokens1.union(tokens2) else 0.0
        
        # Method 2: Sequence-based similarity (n-grams)
        n = 3  # trigrams
        ngrams1 = set([code1_normalized[i:i+n] for i in range(len(code1_normalized)-n+1)])
        ngrams2 = set([code2_normalized[i:i+n] for i in range(len(code2_normalized)-n+1)])
        
        if ngrams1 and ngrams2:
            ngram_similarity = len(ngrams1.intersection(ngrams2)) / len(ngrams1.union(ngrams2))
        else:
            ngram_similarity = 0.0
        
        # Method 3: Line-by-line comparison
        lines1 = [line.strip() for line in code1_normalized.split('\n') if line.strip()]
        lines2 = [line.strip() for line in code2_normalized.split('\n') if line.strip()]
        
        if not lines1 or not lines2:
            line_similarity = 0.0
        else:
            matching_lines = sum(1 for line in lines1 if line in lines2)
            line_similarity = (matching_lines * 2) / (len(lines1) + len(lines2))
        
        # Weighted average of all methods
        similarity = (jaccard * 0.4) + (ngram_similarity * 0.4) + (line_similarity * 0.2)
        
        return min(similarity, 1.0)  # Cap at 1.0
    
    def _normalize_code(self, code):
        """
        Normalize code by removing comments, extra whitespace, and standardizing.
        """
        import re
        
        # Remove single-line comments
        code = re.sub(r'//.*?$', '', code, flags=re.MULTILINE)
        code = re.sub(r'#.*?$', '', code, flags=re.MULTILINE)
        
        # Remove multi-line comments
        code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
        code = re.sub(r'""".*?"""', '', code, flags=re.DOTALL)
        code = re.sub(r"'''.*?'''", '', code, flags=re.DOTALL)
        
        # Normalize whitespace
        code = re.sub(r'\s+', ' ', code)
        code = code.strip()
        
        return code
    
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
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.lib import colors
            from reportlab.lib.enums import TA_CENTER, TA_LEFT
            
            # Create PDF
            filename = f"submission_report_{submission.id}.pdf"
            filepath = os.path.join(settings.MEDIA_ROOT, 'exports', filename)
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            doc = SimpleDocTemplate(filepath, pagesize=letter)
            styles = getSampleStyleSheet()
            story = []
            
            # Custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Title'],
                fontSize=24,
                textColor=colors.HexColor('#981e32'),  # WSU Crimson
                spaceAfter=30,
                alignment=TA_CENTER
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading1'],
                fontSize=16,
                textColor=colors.HexColor('#5c6b73'),  # WSU Gray
                spaceAfter=12
            )
            
            # Title
            title = Paragraph(f"Code Review Report: {submission.assignment.title}", title_style)
            story.append(title)
            story.append(Spacer(1, 0.3*inch))
            
            # Student info
            student_info = Paragraph(
                f"<b>Student:</b> {submission.student.get_full_name()}<br/>"
                f"<b>Submission Date:</b> {submission.submitted_at.strftime('%Y-%m-%d %H:%M:%S')}<br/>"
                f"<b>File:</b> {submission.filename}<br/>"
                f"<b>Attempt:</b> {submission.attempt_number}",
                styles['Normal']
            )
            story.append(student_info)
            story.append(Spacer(1, 0.3*inch))
            
            # Feedback summary
            feedback_items = submission.feedback_items.filter(status='approved')
            critical_count = feedback_items.filter(severity='critical').count()
            warning_count = feedback_items.filter(severity='warning').count()
            suggestion_count = feedback_items.filter(severity='suggestion').count()
            
            summary_data = [
                ['Severity', 'Count'],
                ['Critical', str(critical_count)],
                ['Warning', str(warning_count)],
                ['Suggestion', str(suggestion_count)],
                ['Total', str(feedback_items.count())]
            ]
            
            summary_table = Table(summary_data, colWidths=[2*inch, 1*inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#981e32')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(summary_table)
            story.append(Spacer(1, 0.3*inch))
            
            # Feedback items
            if feedback_items.exists():
                heading = Paragraph("Detailed Feedback", heading_style)
                story.append(heading)
                story.append(Spacer(1, 0.2*inch))
                
                for feedback in feedback_items:
                    severity_color = {
                        'critical': colors.red,
                        'warning': colors.orange,
                        'suggestion': colors.blue
                    }.get(feedback.severity, colors.black)
                    
                    feedback_text = (
                        f"<b>Line {feedback.line_number}</b> "
                        f"<font color='{severity_color.hexval()}'><b>[{feedback.severity.upper()}]</b></font><br/>"
                        f"<b>Category:</b> {feedback.category}<br/>"
                        f"{feedback.message}"
                    )
                    if feedback.instructor_notes:
                        feedback_text += f"<br/><i>Instructor Note: {feedback.instructor_notes}</i>"
                    
                    story.append(Paragraph(feedback_text, styles['Normal']))
                    story.append(Spacer(1, 0.15*inch))
            else:
                story.append(Paragraph("No approved feedback available.", styles['Normal']))
            
            doc.build(story)
            
            return filepath
            
        except ImportError:
            # Fallback to simple text-based PDF if reportlab not available
            filename = f"submission_report_{submission.id}.txt"
            filepath = os.path.join(settings.MEDIA_ROOT, 'exports', filename)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"Code Review Report: {submission.assignment.title}\n")
                f.write("=" * 60 + "\n\n")
                f.write(f"Student: {submission.student.get_full_name()}\n")
                f.write(f"Submission Date: {submission.submitted_at}\n")
                f.write(f"File: {submission.filename}\n")
                f.write(f"Attempt: {submission.attempt_number}\n\n")
                
                feedback_items = submission.feedback_items.filter(status='approved')
                for feedback in feedback_items:
                    f.write(f"Line {feedback.line_number} [{feedback.severity}]: {feedback.message}\n")
            
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
