// Dynamic transcription endpoint based on hostname
const TRANSCRIPTION_ENDPOINT = window.location.hostname === 'localhost' 
    ? 'http://localhost:5001/transcribe' 
    : 'https://hebrew-audio-transcription.onrender.com/transcribe';

console.log('Transcription Endpoint:', TRANSCRIPTION_ENDPOINT);

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

// Transcribe button click event
transcribeBtn.addEventListener('click', async () => {
    if (!selectedFile) {
        alert('אנא בחר קובץ אודיו');
        return;
    }

    // Try multiple FormData configurations
    const formDataConfigs = [
        { key: 'file', data: new FormData() },
        { key: 'audio', data: new FormData() },
        { key: 'audioFile', data: new FormData() }
    ];

    // Append file to each configuration
    formDataConfigs.forEach(config => {
        config.data.append(config.key, selectedFile);
    });

    try {
        for (const config of formDataConfigs) {
            console.log(`Attempting upload with key: ${config.key}`);
            console.log('File Details:', {
                name: selectedFile.name,
                type: selectedFile.type,
                size: selectedFile.size
            });

            transcribeBtn.disabled = true;
            loadingAnimation.style.display = 'inline-block';
            transcriptionText.textContent = '';

            try {
                const response = await fetch(TRANSCRIPTION_ENDPOINT, {
                    method: 'POST',
                    body: config.data
                });

                console.log('Response status:', response.status);
                console.log('Response headers:', Object.fromEntries(response.headers.entries()));

                if (response.ok) {
                    const data = await response.json();
                    transcriptionText.textContent = data.transcription || 'לא התקבל טקסט';
                    return; // Exit after successful upload
                } else {
                    const errorText = await response.text();
                    console.error(`Error with key ${config.key}:`, errorText);
                }
            } catch (innerError) {
                console.error(`Error with key ${config.key}:`, innerError);
            }
        }

        // If all attempts fail
        throw new Error('כל ניסיונות ההעלאה נכשלו');
    } catch (error) {
        console.error('Full error:', error);
        transcriptionText.textContent = `שגיאה: ${error.message}`;
    } finally {
        transcribeBtn.disabled = false;
        loadingAnimation.style.display = 'none';
    }
});