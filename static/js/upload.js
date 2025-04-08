/**
 * Google Drive Upload App - Upload JavaScript
 */

// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize direct file upload
    const directUploadForm = document.getElementById('direct-upload-form');
    if (directUploadForm) {
        directUploadForm.addEventListener('submit', handleDirectUpload);
    }
    
    // Initialize URL upload
    const urlUploadForm = document.getElementById('url-upload-form');
    if (urlUploadForm) {
        urlUploadForm.addEventListener('submit', handleUrlUpload);
    }
    
    // Initialize YouTube upload
    const youtubeUploadForm = document.getElementById('youtube-upload-form');
    if (youtubeUploadForm) {
        youtubeUploadForm.addEventListener('submit', handleYoutubeUpload);
    }
});

/**
 * Handle direct file upload
 * @param {Event} event - Form submit event
 */
function handleDirectUpload(event) {
    event.preventDefault();
    
    const form = event.target;
    const fileInput = form.querySelector('input[type="file"]');
    const progressBar = document.querySelector('#direct-upload-progress');
    const progressBarInner = progressBar.querySelector('.progress-bar');
    
    // Validate file selection
    if (!fileInput.files.length) {
        showModal('Error', 'Please select a file to upload.');
        return;
    }
    
    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append('file', file);
    
    // Show progress bar
    progressBar.classList.remove('d-none');
    progressBarInner.style.width = '0%';
    progressBarInner.setAttribute('aria-valuenow', 0);
    
    // Start upload
    const xhr = new XMLHttpRequest();
    
    // Progress listener
    xhr.upload.addEventListener('progress', function(e) {
        if (e.lengthComputable) {
            const percentComplete = Math.round((e.loaded / e.total) * 100);
            progressBarInner.style.width = percentComplete + '%';
            progressBarInner.setAttribute('aria-valuenow', percentComplete);
            progressBarInner.textContent = percentComplete + '%';
        }
    });
    
    // Load listener
    xhr.addEventListener('load', function() {
        if (xhr.status >= 200 && xhr.status < 300) {
            const response = JSON.parse(xhr.responseText);
            showModal('Success', `File "${file.name}" has been uploaded successfully!`);
            form.reset();
        } else {
            let errorMessage = 'Upload failed.';
            try {
                const response = JSON.parse(xhr.responseText);
                errorMessage = response.error || errorMessage;
            } catch (e) {
                // Use default error message
            }
            showModal('Error', errorMessage);
        }
        progressBar.classList.add('d-none');
    });
    
    // Error listener
    xhr.addEventListener('error', function() {
        showModal('Error', 'An error occurred during the upload. Please try again.');
        progressBar.classList.add('d-none');
    });
    
    // Open and send the request
    xhr.open('POST', '/upload/file', true);
    xhr.send(formData);
}

/**
 * Handle URL upload
 * @param {Event} event - Form submit event
 */
function handleUrlUpload(event) {
    event.preventDefault();
    
    const form = event.target;
    const urlInput = form.querySelector('input[name="url"]');
    const progressBar = document.querySelector('#url-upload-progress');
    const progressBarInner = progressBar.querySelector('.progress-bar');
    
    // Validate URL
    if (!urlInput.value) {
        showModal('Error', 'Please enter a URL.');
        return;
    }
    
    // Show progress bar
    progressBar.classList.remove('d-none');
    progressBarInner.style.width = '0%';
    progressBarInner.setAttribute('aria-valuenow', 0);
    
    // Start interval to simulate progress (since we can't track actual progress for URL uploads)
    let progress = 0;
    const progressInterval = setInterval(function() {
        progress += 5;
        if (progress > 90) {
            clearInterval(progressInterval);
        }
        progressBarInner.style.width = progress + '%';
        progressBarInner.setAttribute('aria-valuenow', progress);
        progressBarInner.textContent = progress + '%';
    }, 500);
    
    // Create form data
    const formData = new FormData();
    formData.append('url', urlInput.value);
    
    // Send request
    fetch('/upload/url', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        clearInterval(progressInterval);
        progressBarInner.style.width = '100%';
        progressBarInner.setAttribute('aria-valuenow', 100);
        progressBarInner.textContent = '100%';
        
        if (data.success) {
            showModal('Success', data.message);
            form.reset();
        } else {
            showModal('Error', data.error || 'Upload failed. Please try again.');
        }
        
        setTimeout(() => {
            progressBar.classList.add('d-none');
        }, 1000);
    })
    .catch(error => {
        clearInterval(progressInterval);
        progressBar.classList.add('d-none');
        showModal('Error', 'An error occurred during the upload. Please try again.');
        console.error('Upload error:', error);
    });
}

/**
 * Handle YouTube upload
 * @param {Event} event - Form submit event
 */
function handleYoutubeUpload(event) {
    event.preventDefault();
    
    const form = event.target;
    const youtubeUrlInput = form.querySelector('input[name="youtube_url"]');
    const progressBar = document.querySelector('#youtube-upload-progress');
    const progressBarInner = progressBar.querySelector('.progress-bar');
    
    // Validate YouTube URL
    if (!youtubeUrlInput.value) {
        showModal('Error', 'Please enter a YouTube URL.');
        return;
    }
    
    // Show progress bar
    progressBar.classList.remove('d-none');
    progressBarInner.style.width = '0%';
    progressBarInner.setAttribute('aria-valuenow', 0);
    
    // Show warning that this might take a while
    showModal('Processing', 'Downloading and processing YouTube video. This may take several minutes depending on the video size.');
    
    // Start interval to simulate progress
    let progress = 0;
    const progressInterval = setInterval(function() {
        progress += 2;
        if (progress > 95) {
            clearInterval(progressInterval);
        }
        progressBarInner.style.width = progress + '%';
        progressBarInner.setAttribute('aria-valuenow', progress);
        progressBarInner.textContent = progress + '%';
    }, 1000);
    
    // Create form data
    const formData = new FormData();
    formData.append('youtube_url', youtubeUrlInput.value);
    
    // Send request
    fetch('/upload/youtube', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        clearInterval(progressInterval);
        progressBarInner.style.width = '100%';
        progressBarInner.setAttribute('aria-valuenow', 100);
        progressBarInner.textContent = '100%';
        
        if (data.success) {
            showModal('Success', data.message);
            form.reset();
        } else {
            showModal('Error', data.error || 'Upload failed. Please try again.');
        }
        
        setTimeout(() => {
            progressBar.classList.add('d-none');
        }, 1000);
    })
    .catch(error => {
        clearInterval(progressInterval);
        progressBar.classList.add('d-none');
        showModal('Error', 'An error occurred during the upload. Please try again.');
        console.error('Upload error:', error);
    });
}

/**
 * Show modal with message
 * @param {string} title - Modal title
 * @param {string} message - Modal message
 * @param {boolean} isHTML - Whether message contains HTML
 */
function showModal(title, message, isHTML = false) {
    const modal = new bootstrap.Modal(document.getElementById('responseModal'));
    const modalTitle = document.getElementById('responseModalLabel');
    const modalBody = document.getElementById('responseModalBody');
    
    modalTitle.textContent = title;
    
    if (isHTML) {
        modalBody.innerHTML = message;
    } else {
        modalBody.textContent = message;
    }
    
    modal.show();
}
