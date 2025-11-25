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
  
  // Helper function to extract data from paginated API responses
  function extractDataFromResponse(response) {
    // Check if response is paginated (has 'results' property)
    if (response && typeof response === 'object' && 'results' in response) {
      return response.results;
    }
    // If it's already an array, return it
    if (Array.isArray(response)) {
      return response;
    }
    // Otherwise return empty array
    return [];
  }
  
  // Data loading functions
  function loadAssignments() {
    return apiRequest('/assignments/').then(function(response) {
      return extractDataFromResponse(response);
    });
  }
  
  function loadCourses() {
    return apiRequest('/courses/').then(function(response) {
      return extractDataFromResponse(response);
    });
  }
  
  function loadSubmissions() {
    return apiRequest('/submissions/').then(function(response) {
      return extractDataFromResponse(response);
    });
  }
  
  function loadFeedback() {
    return apiRequest('/feedback/').then(function(response) {
      return extractDataFromResponse(response);
    });
  }
  
  function loadPlagiarismReports() {
    return apiRequest('/plagiarism/').then(function(response) {
      return extractDataFromResponse(response);
    });
  }
  
  // Upload functions
  function uploadFile(file, assignmentId) {
    var formData = new FormData();
    formData.append('file', file);
    formData.append('assignment_id', assignmentId);
    
    // Get CSRF token
    var csrfToken = getCookie('csrftoken');
    
    return fetch(API_BASE + '/upload/', {
      method: 'POST',
      credentials: 'include',
      headers: {
        'X-CSRFToken': csrfToken
        // Don't set Content-Type - browser will set it automatically with boundary for FormData
      },
      body: formData
    }).then(function(response) {
      if (!response.ok) {
        throw new Error('HTTP ' + response.status);
      }
      return response.json();
    });
  }
  
  // Assignment handlers setup function (global scope)
  function setupAssignmentHandlers() {
    var createAssignmentBtn = document.getElementById('create-assignment-btn');
    if (createAssignmentBtn) {
      // Remove any existing listeners by cloning
      var newBtn = createAssignmentBtn.cloneNode(true);
      createAssignmentBtn.parentNode.replaceChild(newBtn, createAssignmentBtn);
      
      newBtn.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        console.log('Create assignment button clicked');
        
        var assignmentFormContainer = document.getElementById('assignment-form-container');
        var assignmentForm = document.getElementById('assignment-form');
        var assignmentMessage = document.getElementById('assignment-message');
        
        if (!assignmentFormContainer) {
          console.error('Assignment form container not found');
          return;
        }
        
        var isHidden = assignmentFormContainer.style.display === 'none' || 
                      assignmentFormContainer.style.display === '' ||
                      window.getComputedStyle(assignmentFormContainer).display === 'none';
        
        assignmentFormContainer.style.display = isHidden ? 'block' : 'none';
        
        if (isHidden) {
          console.log('Showing assignment form');
          loadCoursesForDropdown();
          if (assignmentForm) {
            assignmentForm.reset();
          }
          if (assignmentMessage) {
            setMessage(assignmentMessage, '', '');
          }
        } else {
          console.log('Hiding assignment form');
        }
      });
    }
    
    var cancelAssignmentBtn = document.getElementById('cancel-assignment-btn');
    if (cancelAssignmentBtn) {
      var newCancelBtn = cancelAssignmentBtn.cloneNode(true);
      cancelAssignmentBtn.parentNode.replaceChild(newCancelBtn, cancelAssignmentBtn);
      
      newCancelBtn.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        
        var assignmentFormContainer = document.getElementById('assignment-form-container');
        var assignmentForm = document.getElementById('assignment-form');
        var assignmentMessage = document.getElementById('assignment-message');
        
        if (assignmentFormContainer) {
          assignmentFormContainer.style.display = 'none';
        }
        if (assignmentForm) {
          assignmentForm.reset();
        }
        if (assignmentMessage) {
          setMessage(assignmentMessage, '', '');
        }
      });
    }
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
      
      html += '<div style="margin-top: 30px; text-align: center;">';
      html += '<button class="btn-primary" data-navigate-to="assignments" style="padding: 12px 24px; font-size: 16px;">Create New Assignment</button>';
      html += '</div>';
    }
    
    html += '</div>';
    dashboardContent.innerHTML = html;
  }
  
  // Assignment management functions
  function displayAssignments() {
    var assignmentsContent = document.getElementById('assignments-content');
    if (!assignmentsContent) return;
    
    var listContent = document.getElementById('assignments-list-content');
    if (!listContent) return;
    
    listContent.innerHTML = '<p>Loading assignments...</p>';
    
    loadAssignments().then(function(data) {
      // Ensure data is an array
      assignments = Array.isArray(data) ? data : [];
      console.log('Loaded assignments:', assignments);
      
      if (!assignments || assignments.length === 0) {
        listContent.innerHTML = '<p>No assignments created yet. Click "Create New Assignment" to get started.</p>';
      return;
    }

      var html = '<div class="assignments-grid">';
      assignments.forEach(function(assignment) {
        html += '<div class="assignment-card">';
        html += '<h4>' + (assignment.title || 'Untitled Assignment') + '</h4>';
        if (assignment.description) {
          html += '<p>' + assignment.description.substring(0, 100) + (assignment.description.length > 100 ? '...' : '') + '</p>';
        }
        html += '<div class="assignment-meta">';
        if (assignment.course_name) {
          html += '<span class="meta-item">Course: ' + assignment.course_name + '</span>';
        }
        html += '<span class="meta-item">Submissions: ' + (assignment.submission_count || 0) + '</span>';
        html += '<span class="meta-item">Max: ' + (assignment.max_submissions || 3) + '</span>';
        if (assignment.due_date) {
          var dueDate = new Date(assignment.due_date);
          html += '<span class="meta-item">Due: ' + dueDate.toLocaleDateString() + '</span>';
        }
        html += '</div>';
        html += '</div>';
      });
      html += '</div>';
      listContent.innerHTML = html;
    }).catch(function(error) {
      console.error('Error loading assignments:', error);
      var listContent = document.getElementById('assignments-list-content');
      if (listContent) {
        listContent.innerHTML = '<p style="color: red;">Error loading assignments: ' + (error.message || 'Unknown error') + '</p>';
      }
    });
  }
  
  function createAssignment(assignmentData) {
    return apiRequest('/assignments/', {
      method: 'POST',
      body: JSON.stringify(assignmentData)
    });
  }
  
  function loadCoursesForDropdown() {
    if (currentUser && currentUser.role === 'instructor') {
      loadCourses().then(function(courses) {
        // Ensure courses is an array
        courses = Array.isArray(courses) ? courses : [];
        var courseSelect = document.getElementById('assignment-course');
        if (courseSelect) {
          // Keep the "No course" option
          var noCourseOption = courseSelect.querySelector('option[value=""]');
          courseSelect.innerHTML = '';
          if (noCourseOption) {
            courseSelect.appendChild(noCourseOption);
          } else {
            var option = document.createElement('option');
            option.value = '';
            option.textContent = 'No course (standalone assignment)';
            courseSelect.appendChild(option);
          }
          
          courses.forEach(function(course) {
            var option = document.createElement('option');
            option.value = course.id;
            option.textContent = course.code + ' - ' + course.name;
            courseSelect.appendChild(option);
          });
        }
      }).catch(function(error) {
        console.error('Error loading courses:', error);
      });
    }
  }
  
  function displayFeedback() {
    if (feedback.length === 0) {
      feedbackContent.innerHTML = '<div class="no-feedback"><p>No feedback available yet. Feedback will appear here once your instructor approves it.</p></div>';
      return;
    }

    // Group feedback by submission
    var feedbackBySubmission = {};
    feedback.forEach(function(item) {
      var subId = item.submission;
      if (!feedbackBySubmission[subId]) {
        feedbackBySubmission[subId] = {
          submission: item.submission,
          title: item.submission_title,
          student: item.student_name,
          items: []
        };
      }
      feedbackBySubmission[subId].items.push(item);
    });

    var html = '<div class="feedback-container">';
    
    Object.keys(feedbackBySubmission).forEach(function(subId) {
      var subFeedback = feedbackBySubmission[subId];
      html += '<div class="feedback-submission">';
      html += '<div class="feedback-submission-header">';
      html += '<h3>' + subFeedback.title + '</h3>';
      html += '<button class="btn-view-code" data-submission-id="' + subId + '">View Code</button>';
      html += '<button class="btn-export-pdf" data-submission-id="' + subId + '">Export PDF</button>';
      html += '</div>';
      
      // Summary stats
      var critical = subFeedback.items.filter(function(f) { return f.severity === 'critical'; }).length;
      var warning = subFeedback.items.filter(function(f) { return f.severity === 'warning'; }).length;
      var suggestion = subFeedback.items.filter(function(f) { return f.severity === 'suggestion'; }).length;
      
      html += '<div class="feedback-stats">';
      html += '<span class="stat-badge critical">' + critical + ' Critical</span>';
      html += '<span class="stat-badge warning">' + warning + ' Warnings</span>';
      html += '<span class="stat-badge suggestion">' + suggestion + ' Suggestions</span>';
      html += '</div>';
      
      html += '<div class="feedback-list">';
      subFeedback.items.forEach(function(item) {
        html += '<div class="feedback-item ' + item.severity + '">';
        html += '<div class="feedback-header">';
        html += '<span class="feedback-line">Line ' + item.line_number + '</span>';
        html += '<span class="feedback-severity ' + item.severity + '">' + item.severity + '</span>';
        html += '<span class="feedback-category">' + item.category + '</span>';
        html += '</div>';
        html += '<div class="feedback-message">' + escapeHtml(item.message) + '</div>';
        if (item.instructor_notes) {
          html += '<div class="instructor-notes"><strong>Instructor Note:</strong> ' + escapeHtml(item.instructor_notes) + '</div>';
        }
        html += '</div>';
      });
      html += '</div>';
      html += '</div>';
    });
    
    html += '</div>';
    feedbackContent.innerHTML = html;
    
    // Add event listeners
    feedbackContent.querySelectorAll('.btn-view-code').forEach(function(btn) {
      btn.addEventListener('click', function() {
        viewCodeWithFeedback(btn.dataset.submissionId);
      });
    });
    
    feedbackContent.querySelectorAll('.btn-export-pdf').forEach(function(btn) {
      btn.addEventListener('click', function() {
        exportSubmission(btn.dataset.submissionId, 'pdf');
      });
    });
  }
  
  function escapeHtml(text) {
    var div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
  
  function viewCodeWithFeedback(submissionId) {
    apiRequest('/submissions/' + submissionId + '/code/').then(function(data) {
      displayCodeViewer(data);
    }).catch(function(error) {
      console.error('Error loading code:', error);
      alert('Failed to load code. Please try again.');
    });
  }
  
  function displayCodeViewer(codeData) {
    var html = '<div class="code-viewer-container">';
    html += '<div class="code-viewer-header">';
    html += '<h3>' + codeData.filename + '</h3>';
    html += '<button class="btn-close-viewer">Close</button>';
    html += '</div>';
    html += '<div class="code-viewer">';
    html += '<pre class="code-content"><code>';
    
    codeData.code.forEach(function(line) {
      var lineClass = '';
      if (line.feedback.length > 0) {
        var severities = line.feedback.map(function(f) { return f.severity; });
        if (severities.includes('critical')) lineClass = 'line-critical';
        else if (severities.includes('warning')) lineClass = 'line-warning';
        else lineClass = 'line-suggestion';
      }
      
      html += '<div class="code-line ' + lineClass + '" data-line="' + line.line_number + '">';
      html += '<span class="line-number">' + line.line_number + '</span>';
      html += '<span class="line-content">' + escapeHtml(line.content) + '</span>';
      
      if (line.feedback.length > 0) {
        html += '<div class="line-feedback">';
        line.feedback.forEach(function(f) {
          html += '<div class="inline-feedback ' + f.severity + '">';
          html += '<span class="feedback-icon">' + (f.severity === 'critical' ? '⚠️' : f.severity === 'warning' ? '⚡' : '💡') + '</span>';
          html += '<span class="feedback-text">' + escapeHtml(f.message) + '</span>';
          html += '</div>';
        });
        html += '</div>';
      }
      
      html += '</div>';
    });
    
    html += '</code></pre>';
    html += '</div>';
    html += '</div>';
    
    // Create modal overlay
    var modal = document.createElement('div');
    modal.className = 'code-viewer-modal';
    modal.innerHTML = html;
    document.body.appendChild(modal);
    
    // Close button
    modal.querySelector('.btn-close-viewer').addEventListener('click', function() {
      document.body.removeChild(modal);
    });
    
    // Close on overlay click
    modal.addEventListener('click', function(e) {
      if (e.target === modal) {
        document.body.removeChild(modal);
      }
    });
  }
  
  function exportSubmission(submissionId, format) {
    var formData = new FormData();
    formData.append('export_type', format);
    formData.append('submission_id', submissionId);
    
    fetch(API_BASE + '/export/', {
      method: 'POST',
      credentials: 'include',
      body: formData,
      headers: {
        'X-CSRFToken': getCookie('csrftoken')
      }
    }).then(function(response) {
      if (response.ok) {
        return response.blob();
      }
      throw new Error('Export failed');
    }).then(function(blob) {
      var url = window.URL.createObjectURL(blob);
      var a = document.createElement('a');
      a.href = url;
      a.download = 'submission_report_' + submissionId + '.' + format;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    }).catch(function(error) {
      console.error('Export error:', error);
      alert('Export failed. Please try again.');
    });
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
      html += '<p><strong>Attempt:</strong> ' + submission.attempt_number + '</p>';
      html += '<p><strong>File:</strong> ' + submission.filename + '</p>';
      html += '<p><strong>Submitted:</strong> ' + new Date(submission.submitted_at).toLocaleString() + '</p>';
      if (submission.feedback_count !== undefined) {
        html += '<p><strong>Feedback Items:</strong> ' + submission.feedback_count + '</p>';
      }
      html += '</div>';
      html += '<div class="submission-actions">';
      html += '<button class="btn-view-submission" data-submission-id="' + submission.id + '">View Code</button>';
      if (submission.status === 'feedback_ready') {
        html += '<button class="btn-export-submission" data-submission-id="' + submission.id + '">Export PDF</button>';
      }
      html += '</div>';
      html += '</div>';
    });
    html += '</div>';
    
    historyContent.innerHTML = html;
    
    // Add event listeners
    historyContent.querySelectorAll('.btn-view-submission').forEach(function(btn) {
      btn.addEventListener('click', function() {
        viewCodeWithFeedback(btn.dataset.submissionId);
      });
    });
    
    historyContent.querySelectorAll('.btn-export-submission').forEach(function(btn) {
      btn.addEventListener('click', function() {
        exportSubmission(btn.dataset.submissionId, 'pdf');
      });
    });
  }
  
  function displayReviewQueue() {
    var pendingFeedback = feedback.filter(function(f) { return f.status === 'pending'; });
    
    if (pendingFeedback.length === 0) {
      reviewContent.innerHTML = '<div class="no-pending"><p>No pending feedback to review. All caught up! 🎉</p></div>';
      return;
    }

    // Group by submission
    var feedbackBySubmission = {};
    pendingFeedback.forEach(function(item) {
      var subId = item.submission;
      if (!feedbackBySubmission[subId]) {
        feedbackBySubmission[subId] = {
          submission: subId,
          title: item.submission_title,
          student: item.student_name,
          items: []
        };
      }
      feedbackBySubmission[subId].items.push(item);
    });
    
    var html = '<div class="review-container">';
    html += '<div class="review-summary">';
    html += '<p><strong>' + pendingFeedback.length + '</strong> feedback items pending review across <strong>' + Object.keys(feedbackBySubmission).length + '</strong> submissions</p>';
    html += '<button class="btn-bulk-approve" id="bulk-approve-btn">Bulk Approve All</button>';
    html += '</div>';
    
    Object.keys(feedbackBySubmission).forEach(function(subId) {
      var subFeedback = feedbackBySubmission[subId];
      html += '<div class="review-submission">';
      html += '<div class="review-submission-header">';
      html += '<h3>' + subFeedback.title + ' - ' + subFeedback.student + '</h3>';
      html += '<button class="btn-view-code" data-submission-id="' + subId + '">View Code</button>';
      // Get assignment ID from first item
      var firstItem = subFeedback.items[0];
      if (firstItem && firstItem.assignment_id) {
        html += '<button class="btn-export-csv" data-assignment-id="' + firstItem.assignment_id + '">Export CSV</button>';
      }
      html += '</div>';
      
      html += '<div class="review-list">';
      subFeedback.items.forEach(function(item) {
        html += '<div class="review-item ' + item.severity + '">';
        html += '<div class="review-header">';
        html += '<span class="review-line">Line ' + item.line_number + '</span>';
        html += '<span class="feedback-severity ' + item.severity + '">' + item.severity + '</span>';
        html += '<span class="feedback-category">' + item.category + '</span>';
        html += '</div>';
        html += '<div class="review-content">';
        html += '<p class="review-message">' + escapeHtml(item.message) + '</p>';
        html += '<div class="review-actions">';
        html += '<button class="btn-approve" data-id="' + item.id + '">✓ Approve</button>';
        html += '<button class="btn-reject" data-id="' + item.id + '">✗ Reject</button>';
        html += '<button class="btn-edit" data-id="' + item.id + '">✎ Edit</button>';
        html += '</div>';
        html += '</div>';
        html += '</div>';
      });
      html += '</div>';
      html += '</div>';
    });
    
    html += '</div>';
    reviewContent.innerHTML = html;
    
    // Add event listeners
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
    
    reviewContent.querySelectorAll('.btn-edit').forEach(function(btn) {
      btn.addEventListener('click', function() {
        editFeedback(btn.dataset.id);
      });
    });
    
    reviewContent.querySelectorAll('.btn-view-code').forEach(function(btn) {
      btn.addEventListener('click', function() {
        viewCodeWithFeedback(btn.dataset.submissionId);
      });
    });
    
    reviewContent.querySelectorAll('.btn-export-csv').forEach(function(btn) {
      btn.addEventListener('click', function() {
        exportAssignment(btn.dataset.assignmentId, 'csv');
      });
    });
    
    // Bulk approve
    var bulkApproveBtn = document.getElementById('bulk-approve-btn');
    if (bulkApproveBtn) {
      bulkApproveBtn.addEventListener('click', function() {
        if (confirm('Approve all ' + pendingFeedback.length + ' pending feedback items?')) {
          bulkApproveFeedback(pendingFeedback.map(function(f) { return f.id; }));
        }
      });
    }
  }
  
  function editFeedback(feedbackId) {
    var item = feedback.find(function(f) { return f.id === feedbackId; });
    if (!item) return;
    
    var newMessage = prompt('Edit feedback message:', item.message);
    if (newMessage && newMessage !== item.message) {
      apiRequest('/feedback/' + feedbackId + '/edit/', {
        method: 'POST',
        body: JSON.stringify({ message: newMessage })
      }).then(function() {
        loadFeedback().then(function() {
          displayReviewQueue();
        });
      }).catch(function(error) {
        console.error('Error editing feedback:', error);
        alert('Failed to edit feedback. Please try again.');
      });
    }
  }
  
  function bulkApproveFeedback(feedbackIds) {
    var promises = feedbackIds.map(function(id) {
      return apiRequest('/feedback/' + id + '/approve/', {
        method: 'POST'
      });
    });
    
    Promise.all(promises).then(function() {
      loadFeedback().then(function() {
        displayReviewQueue();
        displayDashboard();
      });
    }).catch(function(error) {
      console.error('Error bulk approving:', error);
      alert('Some feedback items failed to approve. Please try again.');
    });
  }
  
  function exportAssignment(assignmentId, format) {
    if (!assignmentId) {
      alert('Assignment ID not available');
      return;
    }
    
    var formData = new FormData();
    formData.append('export_type', format);
    formData.append('assignment_id', assignmentId);
    
    fetch(API_BASE + '/export/', {
      method: 'POST',
      credentials: 'include',
      body: formData,
      headers: {
        'X-CSRFToken': getCookie('csrftoken')
      }
    }).then(function(response) {
      if (response.ok) {
        return response.blob();
      }
      throw new Error('Export failed');
    }).then(function(blob) {
      var url = window.URL.createObjectURL(blob);
      var a = document.createElement('a');
      a.href = url;
      a.download = 'assignment_data_' + assignmentId + '.' + format;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    }).catch(function(error) {
      console.error('Export error:', error);
      alert('Export failed. Please try again.');
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

    var allowed = ['.py', '.java', '.cpp', '.zip'];
    var ext = file.name.lastIndexOf('.') >= 0 ? file.name.slice(file.name.lastIndexOf('.')).toLowerCase() : '';

    if (allowed.indexOf(ext) === -1) {
      uploadBtn.disabled = true;
      uploadBtn.classList.remove('enabled');
      setMessage(uploadMessage, 'Please upload a supported code file (.py, .java, .cpp) or ZIP archive', 'error');
      return false;
    }

    // Check file size (16MB limit)
    if (file.size > 16 * 1024 * 1024) {
      uploadBtn.disabled = true;
      uploadBtn.classList.remove('enabled');
      setMessage(uploadMessage, 'File size exceeds 16MB limit', 'error');
      return false;
    }

    uploadBtn.disabled = false;
    uploadBtn.classList.add('enabled');
    if (ext === '.zip') {
      setMessage(uploadMessage, 'ZIP file detected. Multiple files will be processed.', 'success');
    } else {
      setMessage(uploadMessage, 'File looks good. Ready to upload.', 'success');
    }
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
      stopAutoRefresh();
      logout().then(function() {
        currentUser = null;
        showLoginForm();
      });
    });
    
    // Assignment handlers are set up when assignments section is shown
    // (setupAssignmentHandlers is defined in global scope)
    
    // Handle assignment form submission
    document.addEventListener('submit', function(e) {
      if (e.target && e.target.id === 'assignment-form') {
        e.preventDefault();
        
        var assignmentMessage = document.getElementById('assignment-message');
        var title = document.getElementById('assignment-title').value.trim();
        
        if (!title) {
          setMessage(assignmentMessage, 'Please enter an assignment title', 'error');
          return;
        }
        
        var assignmentData = {
          title: title,
          description: document.getElementById('assignment-description').value.trim(),
          max_submissions: parseInt(document.getElementById('assignment-max-submissions').value) || 3
        };
        
        var courseId = document.getElementById('assignment-course').value;
        if (courseId) {
          assignmentData.course = courseId;
        }
        
        var dueDate = document.getElementById('assignment-due-date').value;
        if (dueDate) {
          // Convert local datetime to ISO format
          assignmentData.due_date = new Date(dueDate).toISOString();
        }
        
        setMessage(assignmentMessage, 'Creating assignment...', '');
        
        createAssignment(assignmentData).then(function(response) {
          console.log('Assignment created, response:', response);
          setMessage(assignmentMessage, 'Assignment created successfully!', 'success');
          
          var assignmentForm = document.getElementById('assignment-form');
          var assignmentFormContainer = document.getElementById('assignment-form-container');
          
          if (assignmentForm) {
            assignmentForm.reset();
          }
          if (assignmentFormContainer) {
            assignmentFormContainer.style.display = 'none';
          }
          
          // Reload assignments with a small delay to ensure database is updated
          setTimeout(function() {
            loadAssignments().then(function(data) {
              console.log('Reloaded assignments after creation:', data);
              // Ensure data is an array
              assignments = Array.isArray(data) ? data : [];
              // Update dropdown in upload section
              if (assignmentSelect) {
                assignmentSelect.innerHTML = '<option value="">Select an assignment...</option>';
                assignments.forEach(function(assignment) {
                  var option = document.createElement('option');
                  option.value = assignment.id;
                  option.textContent = assignment.title;
                  assignmentSelect.appendChild(option);
                });
              }
              // Refresh assignments list
              displayAssignments();
              // Refresh dashboard
              displayDashboard();
            }).catch(function(error) {
              console.error('Error reloading assignments:', error);
              setMessage(assignmentMessage, 'Assignment created but failed to refresh list. Please refresh the page.', 'error');
            });
          }, 500);
        }).catch(function(error) {
          console.error('Error creating assignment:', error);
          setMessage(assignmentMessage, 'Error creating assignment: ' + (error.message || 'Unknown error'), 'error');
        });
      }
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
          case 'assignments':
            displayAssignments();
            loadCoursesForDropdown();
            setupAssignmentHandlers();
            break;
        }
      });
    });
    
    // Handle navigation buttons in dynamically generated content (like dashboard)
    document.addEventListener('click', function(e) {
      if (e.target && e.target.dataset && e.target.dataset.navigateTo) {
        var section = e.target.dataset.navigateTo;
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
          case 'assignments':
            displayAssignments();
            loadCoursesForDropdown();
            setupAssignmentHandlers();
            break;
        }
      }
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
      console.log('Initial load of assignments:', data);
      // Ensure data is an array
      assignments = Array.isArray(data) ? data : [];
      if (assignmentSelect) {
        assignmentSelect.innerHTML = '<option value="">Select an assignment...</option>';
        assignments.forEach(function(assignment) {
          var option = document.createElement('option');
          option.value = assignment.id;
          option.textContent = assignment.title;
          assignmentSelect.appendChild(option);
        });
      }
      // If on assignments page, refresh the display
      var activeSection = document.querySelector('.section.active');
      if (activeSection && activeSection.id === 'assignments-section') {
        displayAssignments();
      }
    }).catch(function(error) {
      console.error('Error loading assignments in loadAppData:', error);
      assignments = [];
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
    
    if (currentUser && currentUser.role === 'instructor') {
      loadPlagiarismReports().then(function(data) {
        plagiarismReports = data;
        displayPlagiarismReports();
      });
    }
    
    displayDashboard();
    
    // Start auto-refresh for status updates
    startAutoRefresh();
  }
  
  // Auto-refresh for real-time updates
  var autoRefreshInterval = null;
  
  function startAutoRefresh() {
    // Clear existing interval
    if (autoRefreshInterval) {
      clearInterval(autoRefreshInterval);
    }
    
    // Refresh every 30 seconds
    autoRefreshInterval = setInterval(function() {
      if (currentUser) {
        loadSubmissions().then(function(data) {
          submissions = data;
          // Only update display if on relevant section
          var activeSection = document.querySelector('.section.active');
          if (activeSection && activeSection.id === 'history-section') {
            displayHistory();
          }
        });
        
        loadFeedback().then(function(data) {
          feedback = data;
          var activeSection = document.querySelector('.section.active');
          if (activeSection && activeSection.id === 'feedback-section') {
            displayFeedback();
          }
          if (activeSection && activeSection.id === 'review-section') {
            displayReviewQueue();
          }
        });
        
        displayDashboard();
      }
    }, 30000); // 30 seconds
  }
  
  function stopAutoRefresh() {
    if (autoRefreshInterval) {
      clearInterval(autoRefreshInterval);
      autoRefreshInterval = null;
    }
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
