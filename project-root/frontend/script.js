/*
  Upload validation with real backend integration
  - Listens for a chosen file and checks the extension.
  - Only enables the Upload button for .py, .java, or .cpp files.
  - Clicking Upload sends file to backend API for AI code review.
  - Shows real feedback from AI analysis with severity levels.
*/
(function () {
  var fileInput = document.getElementById('file-input');
  var uploadBtn = document.getElementById('upload-btn');
  var message = document.getElementById('message');
  var feedbackSection = document.getElementById('feedback-section');
  var feedbackList = document.getElementById('feedback-list');
  var allowed = ['.py', '.java', '.cpp'];

  function setMessage(text, type) {
    message.textContent = text || '';
    message.className = 'message' + (type ? ' ' + type : '');
  }

  function displayFeedback(feedback) {
    if (!feedback || feedback.length === 0) {
      feedbackSection.style.display = 'none';
      return;
    }

    feedbackList.innerHTML = '';
    
    feedback.forEach(function(item) {
      var feedbackItem = document.createElement('div');
      feedbackItem.className = 'feedback-item ' + item.severity;
      
      feedbackItem.innerHTML = 
        '<div class="feedback-header">' +
          '<span class="feedback-line">Line ' + item.line + '</span>' +
          '<span class="feedback-severity ' + item.severity + '">' + item.severity + '</span>' +
        '</div>' +
        '<div class="feedback-message">' + item.message + '</div>' +
        '<div class="feedback-category">Category: ' + item.category + '</div>';
      
      feedbackList.appendChild(feedbackItem);
    });
    
    feedbackSection.style.display = 'block';
  }

  function getExtension(name) {
    if (!name) return '';
    var dot = name.lastIndexOf('.');
    return dot >= 0 ? name.slice(dot).toLowerCase() : '';
  }

  function validate() {
    var file = fileInput.files && fileInput.files[0];
    if (!file) {
      uploadBtn.disabled = true;
      uploadBtn.classList.remove('enabled');
      setMessage('', '');
      return false;
    }

    var ext = getExtension(file.name);
    var ok = allowed.indexOf(ext) !== -1;

    if (!ok) {
      uploadBtn.disabled = true;
      uploadBtn.classList.remove('enabled');
      setMessage('Please upload a supported code file (.py, .java, .cpp)', 'error');
      return false;
    }

    uploadBtn.disabled = false;
    uploadBtn.classList.add('enabled');
    setMessage('File looks good. Ready to upload.', 'success');
    return true;
  }

  fileInput.addEventListener('change', validate);

  function uploadFile() {
    if (!validate()) return;
    
    var file = fileInput.files[0];
    var formData = new FormData();
    formData.append('file', file);
    
    setMessage('Analysis in progress...', '');
    uploadBtn.disabled = true;
    uploadBtn.textContent = 'Analyzing...';
    
    fetch('http://localhost:5000/api/upload', {
      method: 'POST',
      body: formData
    })
    .then(function(response) {
      return response.json();
    })
    .then(function(data) {
      if (data.success) {
        var feedbackCount = data.analysis ? data.analysis.length : 0;
        var criticalCount = data.analysis ? data.analysis.filter(function(f) { return f.severity === 'critical'; }).length : 0;
        var warningCount = data.analysis ? data.analysis.filter(function(f) { return f.severity === 'warning'; }).length : 0;
        var suggestionCount = data.analysis ? data.analysis.filter(function(f) { return f.severity === 'suggestion'; }).length : 0;
        
        var summary = 'Analysis complete! Found ' + feedbackCount + ' issues: ';
        if (criticalCount > 0) summary += criticalCount + ' critical, ';
        if (warningCount > 0) summary += warningCount + ' warnings, ';
        if (suggestionCount > 0) summary += suggestionCount + ' suggestions.';
        
        setMessage(summary, 'success');
        
        // Display detailed feedback in the UI
        displayFeedback(data.analysis);
        
        // Also log to console for debugging
        console.log('Code Review Results:', data);
      } else {
        setMessage('Error: ' + (data.error || 'Unknown error'), 'error');
        feedbackSection.style.display = 'none';
      }
    })
    .catch(function(error) {
      setMessage('Upload failed: ' + error.message, 'error');
      console.error('Upload error:', error);
    })
    .finally(function() {
      uploadBtn.disabled = false;
      uploadBtn.textContent = 'Upload';
    });
  }

  uploadBtn.addEventListener('click', uploadFile);
})();
