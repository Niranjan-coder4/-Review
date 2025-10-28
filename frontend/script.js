/*
  Complete Code Review System Frontend
  - Handles authentication, file uploads, feedback management, and instructor review
  - Integrates with Django REST API backend
  - Provides role-based access control and real-time updates
*/
(function () {
  // Global state
  var currentUser = null;
  var assignments = [];
  var submissions = [];
  var feedback = [];
  var plagiarismReports = [];
  
  // API configuration
  var API_BASE = 'http://localhost:8000/api';
  
  // DOM elements
  var loginSection = document.getElementById('login-section');
  var mainApp = document.getElementById('main-app');
  var authMessage = document.getElementById('auth-message');
  var loginForm = document.getElementById('login-form');
  var registerForm = document.getElementById('register-form');
  var showRegister = document.getElementById('show-register');
  var showLogin = document.getElementById('show-login');
  var logoutBtn = document.getElementById('logout-btn');
  var userName = document.getElementById('user-name');
  var userRole = document.getElementById('user-role');
  
  // Navigation
  var navBtns = document.querySelectorAll('.nav-btn');
  var sections = document.querySelectorAll('.section');
  
  // Upload elements
  var fileInput = document.getElementById('file-input');
  var uploadBtn = document.getElementById('upload-btn');
  var uploadMessage = document.getElementById('upload-message');
  var assignmentSelect = document.getElementById('assignment-select');
  
  // Content containers
  var dashboardContent = document.getElementById('dashboard-content');
  var feedbackContent = document.getElementById('feedback-content');
  var historyContent = document.getElementById('history-content');
  var reviewContent = document.getElementById('review-content');
  var plagiarismContent = document.getElementById('plagiarism-content');
  
  // Utility functions
  function setMessage(element, text, type) {
    element.textContent = text || '';
    element.className = 'message' + (type ? ' ' + type : '');
  }
  
  function showSection(sectionName) {
    sections.forEach(function(section) {
      section.classList.remove('active');
    });
    navBtns.forEach(function(btn) {
      btn.classList.remove('active');
    });
    
    document.getElementById(sectionName + '-section').classList.add('active');
    document.querySelector('[data-section="' + sectionName + '"]').classList.add('active');
  }
  
  function updateNavigation() {
    navBtns.forEach(function(btn) {
      if (btn.classList.contains('instructor-only')) {
        btn.style.display = currentUser && currentUser.role === 'instructor' ? 'block' : 'none';
      }
    });
  }
  
  // API functions
  function apiRequest(url, options) {
    var defaultOptions = {
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken')
      }
    };
    
    return fetch(API_BASE + url, Object.assign(defaultOptions, options))
      .then(function(response) {
        if (!response.ok) {
          throw new Error('HTTP ' + response.status);
        }
        return response.json();
      });
  }
  
  function getCookie(name) {
    var value = "; " + document.cookie;
    var parts = value.split("; " + name + "=");
    if (parts.length === 2) return parts.pop().split(";").shift();
  }
  
  // Authentication functions
  function login(username, password) {
    return apiRequest('/auth/login/', {
      method: 'POST',
      body: JSON.stringify({ username: username, password: password })
    });
  }
  
  function register(userData) {
    return apiRequest('/auth/register/', {
      method: 'POST',
      body: JSON.stringify(userData)
    });
  }
  
  function logout() {
    return apiRequest('/auth/logout/', {
      method: 'POST'
    });
  }
  
  function getCurrentUser() {
    return apiRequest('/auth/profile/');
  }
  
  // Data loading functions
  function loadAssignments() {
    return apiRequest('/assignments/');
  }
  
  function loadSubmissions() {
    return apiRequest('/submissions/');
  }
  
  function loadFeedback() {
    return apiRequest('/feedback/');
  }
  
  function loadPlagiarismReports() {
    return apiRequest('/plagiarism/');
  }
  
  // Upload functions
  function uploadFile(file, assignmentId) {
    var formData = new FormData();
    formData.append('file', file);
    formData.append('assignment_id', assignmentId);
    
    return fetch(API_BASE + '/upload/', {
      method: 'POST',
      credentials: 'include',
      body: formData
    }).then(function(response) {
      if (!response.ok) {
        throw new Error('HTTP ' + response.status);
      }
      return response.json();
    });
  }
  
  // Display functions
  function displayDashboard() {
    var html = '<div class="dashboard-stats">';
    
    if (currentUser.role === 'student') {
      html += '<div class="stat-card">';
      html += '<h3>My Submissions</h3>';
      html += '<p class="stat-number">' + submissions.length + '</p>';
      html += '</div>';
      
      html += '<div class="stat-card">';
      html += '<h3>Feedback Received</h3>';
      html += '<p class="stat-number">' + feedback.length + '</p>';
      html += '</div>';
    } else if (currentUser.role === 'instructor') {
      html += '<div class="stat-card">';
      html += '<h3>Assignments</h3>';
      html += '<p class="stat-number">' + assignments.length + '</p>';
      html += '</div>';
      
      html += '<div class="stat-card">';
      html += '<h3>Pending Reviews</h3>';
      var pendingCount = feedback.filter(function(f) { return f.status === 'pending'; }).length;
      html += '<p class="stat-number">' + pendingCount + '</p>';
      html += '</div>';
      
      html += '<div class="stat-card">';
      html += '<h3>Plagiarism Flags</h3>';
      html += '<p class="stat-number">' + plagiarismReports.length + '</p>';
      html += '</div>';
    }
    
    html += '</div>';
    dashboardContent.innerHTML = html;
  }
  
  function displayFeedback() {
    if (feedback.length === 0) {
      feedbackContent.innerHTML = '<div class="no-feedback"><p>No feedback available yet.</p></div>';
      return;
    }

    var html = '<div class="feedback-list">';
    feedback.forEach(function(item) {
      html += '<div class="feedback-item ' + item.severity + '">';
      html += '<div class="feedback-header">';
      html += '<span class="feedback-line">Line ' + item.line_number + '</span>';
      html += '<span class="feedback-severity ' + item.severity + '">' + item.severity + '</span>';
      html += '</div>';
      html += '<div class="feedback-message">' + item.message + '</div>';
      html += '<div class="feedback-category">Category: ' + item.category + '</div>';
      if (item.instructor_notes) {
        html += '<div class="instructor-notes">Instructor Note: ' + item.instructor_notes + '</div>';
      }
      html += '</div>';
    });
    html += '</div>';
    
    feedbackContent.innerHTML = html;
  }
  
  function displayHistory() {
    if (submissions.length === 0) {
      historyContent.innerHTML = '<div class="no-history"><p>No submissions yet.</p></div>';
      return;
    }
    
    var html = '<div class="submission-list">';
    submissions.forEach(function(submission) {
      html += '<div class="submission-item">';
      html += '<div class="submission-header">';
      html += '<h4>' + submission.assignment_title + '</h4>';
      html += '<span class="submission-status ' + submission.status + '">' + submission.status + '</span>';
      html += '</div>';
      html += '<div class="submission-details">';
      html += '<p>Attempt: ' + submission.attempt_number + '</p>';
      html += '<p>File: ' + submission.filename + '</p>';
      html += '<p>Submitted: ' + new Date(submission.submitted_at).toLocaleString() + '</p>';
      html += '</div>';
      html += '</div>';
    });
    html += '</div>';
    
    historyContent.innerHTML = html;
  }
  
  function displayReviewQueue() {
    var pendingFeedback = feedback.filter(function(f) { return f.status === 'pending'; });
    
    if (pendingFeedback.length === 0) {
      reviewContent.innerHTML = '<div class="no-pending"><p>No pending feedback to review.</p></div>';
      return;
    }
    
    var html = '<div class="review-list">';
    pendingFeedback.forEach(function(item) {
      html += '<div class="review-item">';
      html += '<div class="review-header">';
      html += '<h4>' + item.submission_title + ' - ' + item.student_name + '</h4>';
      html += '<span class="feedback-severity ' + item.severity + '">' + item.severity + '</span>';
      html += '</div>';
      html += '<div class="review-content">';
      html += '<p><strong>Line ' + item.line_number + ':</strong> ' + item.message + '</p>';
      html += '<div class="review-actions">';
      html += '<button class="btn-approve" data-id="' + item.id + '">Approve</button>';
      html += '<button class="btn-reject" data-id="' + item.id + '">Reject</button>';
      html += '<button class="btn-edit" data-id="' + item.id + '">Edit</button>';
      html += '</div>';
      html += '</div>';
      html += '</div>';
    });
    html += '</div>';
    
    reviewContent.innerHTML = html;
    
    // Add event listeners for review actions
    reviewContent.querySelectorAll('.btn-approve').forEach(function(btn) {
      btn.addEventListener('click', function() {
        approveFeedback(btn.dataset.id);
      });
    });
    
    reviewContent.querySelectorAll('.btn-reject').forEach(function(btn) {
      btn.addEventListener('click', function() {
        rejectFeedback(btn.dataset.id);
      });
    });
  }
  
  function displayPlagiarismReports() {
    if (plagiarismReports.length === 0) {
      plagiarismContent.innerHTML = '<div class="no-plagiarism"><p>No plagiarism reports.</p></div>';
      return;
    }
    
    var html = '<div class="plagiarism-list">';
    plagiarismReports.forEach(function(report) {
      html += '<div class="plagiarism-item">';
      html += '<div class="plagiarism-header">';
      html += '<h4>' + report.submission1_student + ' vs ' + report.submission2_student + '</h4>';
      html += '<span class="similarity-score">' + (report.similarity_score * 100).toFixed(1) + '% similar</span>';
      html += '</div>';
      html += '<div class="plagiarism-details">';
      html += '<p>Assignment: ' + report.assignment_title + '</p>';
      html += '<p>Status: ' + report.status + '</p>';
      html += '<p>Detected: ' + new Date(report.created_at).toLocaleString() + '</p>';
      html += '</div>';
      html += '<div class="plagiarism-actions">';
      html += '<button class="btn-dismiss" data-id="' + report.id + '">Dismiss</button>';
      html += '</div>';
      html += '</div>';
    });
    html += '</div>';
    
    plagiarismContent.innerHTML = html;
    
    // Add event listeners for plagiarism actions
    plagiarismContent.querySelectorAll('.btn-dismiss').forEach(function(btn) {
      btn.addEventListener('click', function() {
        dismissPlagiarismReport(btn.dataset.id);
      });
    });
  }
  
  // Action functions
  function approveFeedback(feedbackId) {
    apiRequest('/feedback/' + feedbackId + '/approve/', {
      method: 'POST'
    }).then(function() {
      loadFeedback().then(function() {
        displayReviewQueue();
        displayFeedback();
      });
    }).catch(function(error) {
      console.error('Error approving feedback:', error);
    });
  }
  
  function rejectFeedback(feedbackId) {
    apiRequest('/feedback/' + feedbackId + '/reject/', {
      method: 'POST'
    }).then(function() {
      loadFeedback().then(function() {
        displayReviewQueue();
        displayFeedback();
      });
    }).catch(function(error) {
      console.error('Error rejecting feedback:', error);
    });
  }
  
  function dismissPlagiarismReport(reportId) {
    apiRequest('/plagiarism/' + reportId + '/dismiss/', {
      method: 'POST'
    }).then(function() {
      loadPlagiarismReports().then(function() {
        displayPlagiarismReports();
      });
    }).catch(function(error) {
      console.error('Error dismissing plagiarism report:', error);
    });
  }
  
  // File validation
  function validateFile() {
    var file = fileInput.files && fileInput.files[0];
    if (!file) {
      uploadBtn.disabled = true;
      uploadBtn.classList.remove('enabled');
      setMessage(uploadMessage, '', '');
      return false;
    }

    var allowed = ['.py', '.java', '.cpp'];
    var ext = file.name.lastIndexOf('.') >= 0 ? file.name.slice(file.name.lastIndexOf('.')).toLowerCase() : '';

    if (allowed.indexOf(ext) === -1) {
      uploadBtn.disabled = true;
      uploadBtn.classList.remove('enabled');
      setMessage(uploadMessage, 'Please upload a supported code file (.py, .java, .cpp)', 'error');
      return false;
    }

    uploadBtn.disabled = false;
    uploadBtn.classList.add('enabled');
    setMessage(uploadMessage, 'File looks good. Ready to upload.', 'success');
    return true;
  }

  // Event listeners
  function initializeEventListeners() {
    // Authentication
    loginForm.addEventListener('submit', function(e) {
      e.preventDefault();
      var username = document.getElementById('username').value;
      var password = document.getElementById('password').value;
      
      login(username, password).then(function(response) {
        if (response.user) {
          currentUser = response.user;
          showMainApp();
        } else {
          setMessage(authMessage, response.message || 'Login failed', 'error');
        }
      }).catch(function(error) {
        setMessage(authMessage, 'Login failed: ' + error.message, 'error');
      });
    });
    
    registerForm.addEventListener('submit', function(e) {
      e.preventDefault();
      var formData = {
        username: document.getElementById('reg-username').value,
        email: document.getElementById('reg-email').value,
        first_name: document.getElementById('reg-first-name').value,
        last_name: document.getElementById('reg-last-name').value,
        role: document.getElementById('reg-role').value,
        student_id: document.getElementById('reg-student-id').value,
        password: document.getElementById('reg-password').value,
        password_confirm: document.getElementById('reg-password-confirm').value
      };
      
      register(formData).then(function(response) {
        if (response.success) {
          currentUser = response.user;
          showMainApp();
        } else {
          setMessage(authMessage, response.message, 'error');
        }
      }).catch(function(error) {
        setMessage(authMessage, 'Registration failed: ' + error.message, 'error');
      });
    });
    
    showRegister.addEventListener('click', function(e) {
      e.preventDefault();
      loginForm.style.display = 'none';
      registerForm.style.display = 'block';
    });
    
    showLogin.addEventListener('click', function(e) {
      e.preventDefault();
      registerForm.style.display = 'none';
      loginForm.style.display = 'block';
    });
    
    logoutBtn.addEventListener('click', function() {
      logout().then(function() {
        currentUser = null;
        showLoginForm();
      });
    });
    
    // Navigation
    navBtns.forEach(function(btn) {
      btn.addEventListener('click', function() {
        var section = btn.dataset.section;
        showSection(section);
        
        // Load section-specific data
        switch(section) {
          case 'dashboard':
            displayDashboard();
            break;
          case 'feedback':
            displayFeedback();
            break;
          case 'history':
            displayHistory();
            break;
          case 'review':
            displayReviewQueue();
            break;
          case 'plagiarism':
            displayPlagiarismReports();
            break;
        }
      });
    });
    
    // File upload
    fileInput.addEventListener('change', validateFile);
    
    uploadBtn.addEventListener('click', function() {
      if (!validateFile()) return;
      
      var file = fileInput.files[0];
      var assignmentId = assignmentSelect.value;
      
      if (!assignmentId) {
        setMessage(uploadMessage, 'Please select an assignment', 'error');
        return;
      }
      
      setMessage(uploadMessage, 'Analysis in progress...', '');
    uploadBtn.disabled = true;
    uploadBtn.textContent = 'Analyzing...';
    
      uploadFile(file, assignmentId).then(function(response) {
        if (response.success) {
          setMessage(uploadMessage, 'Upload successful! Analysis complete.', 'success');
          loadSubmissions().then(function() {
            displayHistory();
          });
        } else {
          setMessage(uploadMessage, 'Error: ' + (response.error || 'Unknown error'), 'error');
        }
      }).catch(function(error) {
        setMessage(uploadMessage, 'Upload failed: ' + error.message, 'error');
      }).finally(function() {
        uploadBtn.disabled = false;
        uploadBtn.textContent = 'Upload';
      });
    });
  }
  
  // App initialization
  function showLoginForm() {
    loginSection.style.display = 'block';
    mainApp.style.display = 'none';
  }
  
  function showMainApp() {
    loginSection.style.display = 'none';
    mainApp.style.display = 'block';
    
    if (currentUser) {
      userName.textContent = currentUser.first_name + ' ' + currentUser.last_name;
      userRole.textContent = currentUser.role;
    } else {
      // If no currentUser, try to get it from profile
      getCurrentUser().then(function(userData) {
        currentUser = userData;
        userName.textContent = currentUser.first_name + ' ' + currentUser.last_name;
        userRole.textContent = currentUser.role;
      }).catch(function(error) {
        console.error('Error getting user profile:', error);
        userName.textContent = 'User';
        userRole.textContent = 'Unknown';
      });
    }
    
    updateNavigation();
    loadAppData();
  }
  
  function loadAppData() {
    // Load assignments for upload dropdown
    loadAssignments().then(function(data) {
      assignments = data;
      assignmentSelect.innerHTML = '<option value="">Select an assignment...</option>';
      assignments.forEach(function(assignment) {
        var option = document.createElement('option');
        option.value = assignment.id;
        option.textContent = assignment.title;
        assignmentSelect.appendChild(option);
      });
    });
    
    // Load user data
    loadSubmissions().then(function(data) {
      submissions = data;
      displayHistory();
    });
    
    loadFeedback().then(function(data) {
      feedback = data;
      displayFeedback();
    });
    
    if (currentUser.role === 'instructor') {
      loadPlagiarismReports().then(function(data) {
        plagiarismReports = data;
        displayPlagiarismReports();
      });
    }
    
    displayDashboard();
  }
  
  // Initialize app
  function init() {
    initializeEventListeners();
    
    // Check if user is already logged in
    getCurrentUser().then(function(response) {
      if (response.success) {
        currentUser = response.user;
        showMainApp();
      } else {
        showLoginForm();
      }
    }).catch(function() {
      showLoginForm();
    });
  }
  
  // Start the application
  init();
})();
