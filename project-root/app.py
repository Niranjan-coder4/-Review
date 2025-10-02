"""
Simple Flask backend for code review
- Handles file uploads (.py, .java, .cpp)
- Integrates with AI service for code analysis
- Returns structured feedback with severity levels
"""

import os
import json
import requests
from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_cors import CORS
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder='frontend', template_folder='frontend')
CORS(app)  # Enable CORS for all routes
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size


# key for session managment
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'supersecretkey')

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'py', 'java', 'cpp'}
AI_API_KEY = os.getenv('AI_API_KEY')
AI_API_URL = os.getenv('AI_API_URL', 'https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium')
# AI_API_URL = os.getenv('AI_API_URL', 'https://api.openai.com/v1/chat/completions')

# Create upload directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Simple hardcoded login credentials for demo
VALID_USERNAME = 'admin'
VALID_PASSWORD = '1234'

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_extension(filename):
    """Get file extension in lowercase"""
    return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

def generate_mock_feedback(code_content, file_extension):
    """Generate mock feedback when no AI service is available"""
    lines = code_content.split('\n')
    feedback = []
    
    # Basic pattern matching for common issues
    for i, line in enumerate(lines, 1):
        line_lower = line.lower().strip()
        
        # Check for common Python issues
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
        
        # Check for common Java issues
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
        
        # Check for common C++ issues
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
    
    # If no issues found, add a general suggestion
    if not feedback:
        feedback.append({
            "line": 1,
            "severity": "suggestion",
            "message": "Code looks good! Consider adding comments for complex logic.",
            "category": "best_practice"
        })
    
    return {"feedback": feedback}

def call_ai_review(code_content, file_extension):
    """Call AI service to review the code"""
    # If no API key, use mock feedback
    if not AI_API_KEY:
        print("No AI API key found, using mock feedback generator")
        return generate_mock_feedback(code_content, file_extension)
    
    # Prepare the prompt based on file type
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

    try:
        headers = {
            'Authorization': f'Bearer {AI_API_KEY}',
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
        
        response = requests.post(AI_API_URL, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        
        ai_response = response.json()
        content = ai_response['choices'][0]['message']['content'].strip()
        
        # Try to parse the JSON response
        try:
            feedback = json.loads(content)
            return {"feedback": feedback}
        except json.JSONDecodeError:
            # If AI didn't return valid JSON, fall back to mock
            print("AI returned invalid JSON, falling back to mock feedback")
            return generate_mock_feedback(code_content, file_extension)
            
    except requests.exceptions.RequestException as e:
        print(f"AI service error: {str(e)}, falling back to mock feedback")
        return generate_mock_feedback(code_content, file_extension)
    except Exception as e:
        print(f"Unexpected error: {str(e)}, falling back to mock feedback")
        return generate_mock_feedback(code_content, file_extension)

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle file upload and return AI review"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Please upload a supported code file (.py, .java, .cpp)'}), 400
    
    try:
        # Save the file
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        # Read file content
        with open(filepath, 'r', encoding='utf-8') as f:
            code_content = f.read()
        
        # Get file extension
        file_extension = get_file_extension(filename)
        
        # Call AI review
        ai_result = call_ai_review(code_content, file_extension)
        
        if 'error' in ai_result:
            return jsonify(ai_result), 500
        
        # Clean up uploaded file
        os.remove(filepath)
        
        # Return success response
        return jsonify({
            'success': True,
            'message': 'Code analysis completed',
            'filename': filename,
            'file_type': file_extension,
            'analysis': ai_result['feedback']
        })
        
    except Exception as e:
        return jsonify({'error': f'Processing error: {str(e)}'}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'ai_configured': bool(AI_API_KEY)
    })


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == VALID_USERNAME and password == VALID_PASSWORD:
            session['user'] = username
            return redirect(url_for('upload_form'))  # Redirect after login
        else:
            return render_template('login.html', error='Invalid credentials')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/upload-form')
def upload_form():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('upload_form.html')


if __name__ == '__main__':
    print("Starting code review backend...")
    print(f"AI API configured: {bool(AI_API_KEY)}")
    print("Upload endpoint: POST /api/upload")
    print("Health check: GET /api/health")
    app.run(debug=False, host='0.0.0.0', port=5000, use_reloader=False)
