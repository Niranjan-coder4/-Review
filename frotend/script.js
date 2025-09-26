/*
  Upload validation (no backend yet)
  - Listens for a chosen file and checks the extension.
  - Only enables the Upload button for .py, .java, or .cpp files.
  - Clicking Upload shows mock messages to simulate the flow.
  - Keeping logic tiny and readable so we can swap in real API calls later.
*/
(function () {
  var fileInput = document.getElementById('file-input');
  var uploadBtn = document.getElementById('upload-btn');
  var message = document.getElementById('message');
  var allowed = ['.py', '.java', '.cpp'];

  function setMessage(text, type) {
    message.textContent = text || '';
    message.className = 'message' + (type ? ' ' + type : '');
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

  uploadBtn.addEventListener('click', function () {
    if (!validate()) return;
    // No real upload yet; simulate success
    setMessage('Analysis in progress... (mock)', '');
    setTimeout(function () {
      setMessage('Upload successful (mock). Instructor review pending.', 'success');
    }, 600);
  });
})();
