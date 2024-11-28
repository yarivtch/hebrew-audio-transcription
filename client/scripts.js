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

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
        console.log('Sending request to:', TRANSCRIPTION_ENDPOINT);
        console.log('File:', selectedFile.name);

        transcribeBtn.disabled = true;
        loadingAnimation.style.display = 'inline-block';
        transcriptionText.textContent = '';

        const response = await fetch(TRANSCRIPTION_ENDPOINT, {
            method: 'POST',
            body: formData
        });

        console.log('Response status:', response.status);
        console.log('Response headers:', Object.fromEntries(response.headers.entries()));

        if (!response.ok) {
            const errorText = await response.text();
            console.error('Error response:', errorText);
            throw new Error(`שגיאה בביצוע התמלול: ${errorText}`);
        }

        const data = await response.json();
        transcriptionText.textContent = data.transcription || 'לא התקבל טקסט';
    } catch (error) {
        console.error('Full error:', error);
        transcriptionText.textContent = `שגיאה: ${error.message}`;
    } finally {
        transcribeBtn.disabled = false;
        loadingAnimation.style.display = 'none';
    }
});