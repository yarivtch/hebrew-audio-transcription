// Determine transcription endpoint dynamically
const TRANSCRIPTION_ENDPOINT = (() => {
    const hostname = window.location.hostname;
    const port = window.location.port;
    
    // Local development
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
        return `http://localhost:${port || 5001}/transcribe`;
    }
    
    // Production (Render) or other hosted environments
    return '/transcribe';
})();

console.log('🌐 Transcription Endpoint:', TRANSCRIPTION_ENDPOINT);

const dropArea = document.getElementById('drop-area');
const transcribeBtn = document.getElementById('transcribe-btn');
const fileInput = document.getElementById('fileElem');
const transcriptionText = document.getElementById('transcription-text');
const loadingAnimation = document.getElementById('loading-animation');
const selectedFileDiv = document.getElementById('selected-file');

let selectedFile = null;

// Prevent default drag behaviors
['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    dropArea.addEventListener(eventName, preventDefaults, false);
});

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

// Highlight drop area when item is dragged over it
['dragenter', 'dragover'].forEach(eventName => {
    dropArea.addEventListener(eventName, highlight, false);
});

['dragleave', 'drop'].forEach(eventName => {
    dropArea.addEventListener(eventName, unhighlight, false);
});

function highlight() {
    dropArea.classList.add('highlight');
}

function unhighlight() {
    dropArea.classList.remove('highlight');
}

// Handle dropped files
dropArea.addEventListener('drop', handleDrop, false);

function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;
    handleFiles(files);
}

function handleFiles(files) {
    if (files.length > 0) {
        selectedFile = files[0];
        updateFileDisplay(selectedFile);
    }
}

function updateFileDisplay(file) {
    selectedFileDiv.textContent = `קובץ נבחר: ${file.name}`;
    transcribeBtn.disabled = false;
}

// File input change event
fileInput.addEventListener('change', function(e) {
    handleFiles(this.files);
});

transcribeBtn.addEventListener('click', () => {
    if (selectedFile) {
        uploadFile(selectedFile);
    }
});

function uploadFile(file) {
    console.log('Uploading File:', {
        name: file.name,
        type: file.type,
        size: file.size
    });

    let formData = new FormData();
    formData.append('audio', file);

    // Log FormData contents
    for (let [key, value] of formData.entries()) {
        console.log(`FormData Entry - Key: ${key}, Value:`, value);
    }

    // Disable transcribe button and show loading
    transcribeBtn.disabled = true;
    loadingAnimation.style.display = 'inline-block';
    transcriptionText.textContent = '';

    fetch(TRANSCRIPTION_ENDPOINT, {
        method: 'POST',
        body: formData
    })
    .then(response => {
        console.log('Response Status:', response.status);
        if (!response.ok) {
            throw new Error('שגיאה בתמלול');
        }
        return response.json();
    })
    .then(data => {
        console.log('Transcription Response:', data);
        transcriptionText.textContent = data.transcription || 'לא התקבל טקסט';
    })
    .catch(error => {
        console.error('Error:', error);
        transcriptionText.textContent = `שגיאה: ${error.message}`;
    })
    .finally(() => {
        // Re-enable transcribe button and hide loading
        transcribeBtn.disabled = false;
        loadingAnimation.style.display = 'none';
    });
};