
document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('uploadForm');
    const fileInput = document.getElementById('fileInput');
    const modeInput = document.getElementById('mode');
    const statusDiv = document.getElementById('status');
    const uploadText = document.querySelector('.file-upload-text');
    const submitBtn = document.querySelector('.btn-primary');

    // 1. File Selection Feedback
    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) {
            uploadText.textContent = `Selected: ${fileInput.files[0].name}`;
            uploadText.style.color = 'var(--primary-color)';
            uploadText.style.fontWeight = '600';
        } else {
            uploadText.textContent = 'Drag & Drop or Click to Upload Image/PDF';
            uploadText.style.color = '#666';
            uploadText.style.fontWeight = 'normal';
        }
    });

    // 2. Form Submission
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        if (fileInput.files.length === 0) {
            showStatus('Please select a file to upload.', 'error');
            return;
        }

        const formData = new FormData();
        formData.append('file', fileInput.files[0]);
        formData.append('mode', modeInput.value);

        // UI: Loading State
        submitBtn.disabled = true;
        submitBtn.innerHTML = 'Processing...';
        showStatus('Analyzing image with AI...', 'loading');

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (result.status === 'success') {
                showStatus('Success! Document Generated.', 'success');
                
                // Add Download Button
                const downloadLink = document.createElement('a');
                downloadLink.href = `/download/${result.download_url}`;
                downloadLink.innerText = 'Download Word Document';
                downloadLink.className = 'download-btn'; // Uses CSS for styling
                downloadLink.target = '_blank';
                
                statusDiv.appendChild(downloadLink);

            } else {
                showStatus(`Error: ${result.message}`, 'error');
            }

        } catch (error) {
            console.error(error);
            showStatus('Connection failed. Please try again.', 'error');
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = 'Analyze & Generate';
        }
    });

    // Helper: Show Status Message
    function showStatus(message, type) {
        statusDiv.innerHTML = ''; // Clear previous

        const msgDiv = document.createElement('div');
        msgDiv.className = `status-message status-${type}`;
        
        if (type === 'loading') {
            msgDiv.innerHTML = `<div class="loader"></div> <span>${message}</span>`;
            msgDiv.classList.add('status-loading');
        } else {
            msgDiv.innerText = message;
        }

        statusDiv.appendChild(msgDiv);
    }
});