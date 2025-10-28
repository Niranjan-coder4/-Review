# //Review Backend API

Complete Django REST API backend for the LLM-powered code review system.

## Features

- **Authentication & Authorization**: Role-based access control (Student/Instructor/Admin)
- **File Upload**: Support for Python, Java, and C++ code files
- **AI Code Analysis**: Integration with LLM APIs for intelligent code review
- **Instructor Approval Workflow**: Mandatory review of all AI-generated feedback
- **Plagiarism Detection**: Automatic similarity checking between submissions
- **Submission History**: Track student progress across multiple attempts
- **Export Functionality**: PDF reports and CSV data export
- **FERPA Compliance**: Secure handling of student data

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Database Setup

Install PostgreSQL and create a database:

```sql
CREATE DATABASE codereview;
CREATE USER postgres WITH PASSWORD 'password';
GRANT ALL PRIVILEGES ON DATABASE codereview TO postgres;
```

### 3. Environment Configuration

Copy the environment template:

```bash
cp env.example .env
```

Edit `.env` with your settings:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
DB_NAME=codereview
DB_USER=postgres
DB_PASSWORD=password
DB_HOST=localhost
DB_PORT=5432
```

### 4. Database Migration

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Create Sample Data (Optional)

```bash
python manage.py create_sample_data
```

This creates test users:
- **Instructor**: `instructor1` / `password123`
- **Student 1**: `student1` / `password123`
- **Student 2**: `student2` / `password123`

### 6. Run the Server

```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000/api/`

## API Endpoints

### Authentication
- `POST /api/auth/login/` - User login
- `POST /api/auth/logout/` - User logout
- `POST /api/auth/register/` - User registration
- `GET /api/auth/profile/` - Get current user profile

### Assignments
- `GET /api/assignments/` - List assignments
- `POST /api/assignments/` - Create assignment (instructor only)
- `GET /api/assignments/{id}/submissions/` - Get submissions for assignment

### Submissions
- `GET /api/submissions/` - List user's submissions
- `POST /api/submissions/` - Create submission
- `GET /api/submissions/{id}/feedback/` - Get feedback for submission
- `GET /api/submissions/{id}/history/` - Get submission history

### Feedback
- `GET /api/feedback/` - List feedback items
- `POST /api/feedback/{id}/approve/` - Approve feedback (instructor only)
- `POST /api/feedback/{id}/reject/` - Reject feedback (instructor only)
- `POST /api/feedback/{id}/edit/` - Edit feedback (instructor only)

### File Upload
- `POST /api/upload/` - Upload code file for analysis

### Plagiarism Reports
- `GET /api/plagiarism/` - List plagiarism reports (instructor only)
- `POST /api/plagiarism/{id}/dismiss/` - Dismiss plagiarism report

### Export Jobs
- `GET /api/exports/` - List export jobs
- `POST /api/exports/` - Create export job

### Health Check
- `GET /api/health/` - System health status

## AI Integration

The system works with or without an AI API key:

### With AI API (Recommended)
Configure your preferred AI service in `.env`:

**OpenAI:**
```env
AI_API_KEY=your_openai_api_key
AI_API_URL=https://api.openai.com/v1/chat/completions
```

**Hugging Face (Free):**
```env
AI_API_KEY=hf_your_token
AI_API_URL=https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium
```

**Groq (Free tier):**
```env
AI_API_KEY=gsk_your_key
AI_API_URL=https://api.groq.com/openai/v1/chat/completions
```

### Without AI API
If no API key is provided, the system uses intelligent pattern-matching to provide code feedback based on common programming issues.

## Database Models

### User
Extended Django User model with role-based access:
- `role`: student, instructor, or admin
- `student_id`: optional student identifier

### Assignment
Represents coding assignments:
- `title`, `description`: assignment details
- `instructor`: assignment creator
- `due_date`: optional deadline
- `max_submissions`: submission limit

### Submission
Student code submissions:
- `assignment`: linked assignment
- `student`: submission author
- `attempt_number`: submission attempt
- `file_content`: code content
- `status`: submission status

### Feedback
AI-generated code feedback:
- `submission`: linked submission
- `line_number`: specific line
- `severity`: critical, warning, or suggestion
- `category`: feedback type
- `status`: approval status

### PlagiarismReport
Plagiarism detection results:
- `submission1`, `submission2`: compared submissions
- `similarity_score`: similarity percentage
- `status`: report status

## Security Features

- **Role-based Access Control**: Users can only access appropriate data
- **CSRF Protection**: Built-in Django CSRF protection
- **Password Validation**: Strong password requirements
- **FERPA Compliance**: Secure student data handling
- **Audit Trail**: Track all feedback approvals/rejections

## Development

### Running Tests
```bash
python manage.py test
```

### Creating Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### Django Admin
Access the admin interface at `http://localhost:8000/admin/`

Create a superuser:
```bash
python manage.py createsuperuser
```

## Production Deployment

For production deployment:

1. Set `DEBUG=False` in `.env`
2. Configure proper database credentials
3. Set up static file serving
4. Configure HTTPS
5. Set up proper logging
6. Use environment variables for secrets

## Troubleshooting

### Common Issues

**Database Connection Error:**
- Ensure PostgreSQL is running
- Check database credentials in `.env`
- Verify database exists

**AI API Errors:**
- Check API key validity
- Verify API URL format
- System falls back to mock feedback if API fails

**File Upload Issues:**
- Check file size limits (16MB default)
- Verify file extensions (.py, .java, .cpp)
- Ensure proper permissions

### Logs
Check Django logs for detailed error information:
```bash
tail -f logs/django.log
```

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review Django logs
3. Verify environment configuration
4. Test with sample data
