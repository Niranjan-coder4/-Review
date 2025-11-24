# //Review - LLM-Powered Code Review System

A comprehensive code review platform that leverages Large Language Models to provide intelligent feedback on student programming assignments. The system ensures instructor oversight through a mandatory approval workflow while automating the preliminary analysis process.

## 🚀 Features

### Core Functionality
- **Multi-Language Support**: Python, Java, and C++ code analysis
- **AI-Powered Analysis**: Intelligent code review with LLM integration
- **Instructor Approval Workflow**: Mandatory review of all AI feedback
- **Role-Based Access**: Student, Instructor, and Admin user roles
- **Submission History**: Track student progress across multiple attempts
- **Plagiarism Detection**: Automatic similarity checking between submissions

### Educational Features
- **Inline Feedback**: Line-specific comments with severity levels
- **Categorized Reports**: Critical, Warning, and Suggestion classifications
- **Export Functionality**: PDF reports and CSV data export
- **FERPA Compliance**: Secure handling of student data
- **Real-time Updates**: Live status tracking for submissions

## 🏗️ Architecture

### Frontend
- **Pure HTML/CSS/JavaScript**: No framework dependencies
- **Responsive Design**: Works on desktop and mobile devices
- **Role-Based UI**: Different interfaces for students and instructors
- **Real-time Updates**: Live feedback and status updates

### Backend
- **Django REST API**: Robust Python backend with RESTful endpoints
- **PostgreSQL Database**: Reliable data persistence
- **AI Integration**: Support for OpenAI, Hugging Face, and Groq APIs
- **Mock Analysis**: Intelligent pattern-matching when AI is unavailable

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- PostgreSQL 12+
- Node.js (for development)

### Backend Setup

1. **Install Dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Database Setup**
   ```sql
   CREATE DATABASE codereview;
   CREATE USER postgres WITH PASSWORD 'password';
   GRANT ALL PRIVILEGES ON DATABASE codereview TO postgres;
   ```

3. **Environment Configuration**
   ```bash
   cp env.example .env
   # Edit .env with your database credentials
   ```

4. **Database Migration**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Create Sample Data**
   ```bash
   python manage.py create_sample_data
   ```

6. **Run Server**
   ```bash
   python manage.py runserver
   ```

### Frontend Setup

1. **Serve Frontend**
   ```bash
   cd frontend
   # Serve with any HTTP server, e.g.:
   python -m http.server 3000
   ```

2. **Access Application**
   - Frontend: `http://localhost:3000`
   - Backend API: `http://localhost:8000/api/`

### Test Accounts
After running `create_sample_data`:
- **Instructor**: `instructor1` / `password123`
- **Student 1**: `student1` / `password123`
- **Student 2**: `student2` / `password123`

## 📋 Requirements Coverage

### ✅ Functional Requirements (100% Complete)
- **FR-1**: Multi-format code upload (.py, .java, .cpp)
- **FR-2**: LLM-powered code analysis with fallback
- **FR-3**: Inline feedback annotation with line numbers
- **FR-4**: Categorized summary reports (Critical/Warning/Suggestion)
- **FR-5**: Instructor approval workflow (Approve/Reject/Edit)
- **FR-6**: Student feedback dashboard with status tracking
- **FR-7**: Submission history with attempt tracking
- **FR-8**: Instructor override capabilities
- **FR-9**: Plagiarism detection with similarity scoring
- **FR-10**: Export functionality (PDF/CSV)

### ✅ Non-Functional Requirements
- **NFR-1**: Performance - Analysis completes in <10 seconds
- **NFR-2**: Reliability - 99.5% uptime target
- **NFR-3**: Security - Role-based access control
- **NFR-4**: FERPA Compliance - Secure student data handling
- **NFR-5**: Scalability - Supports 200+ concurrent users
- **NFR-6**: Usability - 3-click navigation to key features
- **NFR-7**: Maintainability - Modular architecture

## 🔧 Configuration

### AI Integration (Optional)
The system works with or without AI APIs:

**With AI API:**
```env
AI_API_KEY=your_api_key
AI_API_URL=https://api.openai.com/v1/chat/completions
```

**Without AI API:**
The system uses intelligent pattern-matching for code analysis.

### Database Configuration
```env
DB_NAME=codereview
DB_USER=postgres
DB_PASSWORD=password
DB_HOST=localhost
DB_PORT=5432
```

## 📊 System Workflow

1. **Student Upload**: Student uploads code file for assignment
2. **AI Analysis**: System analyzes code using LLM or pattern matching
3. **Feedback Generation**: Creates line-specific feedback with severity levels
4. **Instructor Review**: Instructor approves, rejects, or edits feedback
5. **Student Access**: Student views approved feedback and submission history
6. **Plagiarism Check**: Automatic similarity detection runs in background
7. **Export Options**: Instructor can export reports and data

## 🛠️ Development

### Project Structure
```
├── backend/
│   ├── codereview/          # Django project settings
│   ├── core/               # User models and authentication
│   ├── api/                # REST API endpoints
│   └── manage.py           # Django management
├── frontend/
│   ├── index.html          # Main application interface
│   ├── script.js           # Frontend JavaScript
│   └── styles.css          # Application styles
└── README.md               # This file
```

### API Endpoints
- `POST /api/auth/login/` - User authentication
- `POST /api/upload/` - File upload and analysis
- `GET /api/feedback/` - Retrieve feedback
- `POST /api/feedback/{id}/approve/` - Approve feedback
- `GET /api/plagiarism/` - Plagiarism reports
- `GET /api/health/` - System health check

## 🚀 Deployment

### Production Checklist
- [ ] Set `DEBUG=False` in environment
- [ ] Configure production database
- [ ] Set up HTTPS/SSL certificates
- [ ] Configure static file serving
- [ ] Set up logging and monitoring
- [ ] Configure AI API keys
- [ ] Set up backup procedures

### Docker Deployment (Future)
```dockerfile
# Docker configuration will be added for containerized deployment
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is developed for educational purposes as part of CPT_S 322 - Software Engineering Principles I.

## 👥 Team

- **Niranjan S.** (011847965)
- **Aldric C.** (011852802)
- **Course**: CPT_S 322 - Software Engineering Principles I
- **Instructor**: Parteek Kumar

## 📞 Support

For issues or questions:
1. Check the troubleshooting section in backend README
2. Review Django logs for error details
3. Verify environment configuration
4. Test with sample data

---

**Note**: This system is designed to augment, not replace, instructor judgment. The mandatory approval workflow ensures instructors retain ultimate authority over all feedback while leveraging AI efficiency for preliminary analysis.
