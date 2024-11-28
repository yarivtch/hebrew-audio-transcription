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

// Transcribe button click event
transcribeBtn.addEventListener('click', async () => {
    console.group('📤 Audio File Upload Debugging');
    console.log('Selected File:', selectedFile);

    if (!selectedFile) {
        console.warn('❌ No File Selected');
        alert('אנא בחר קובץ אודיו');
        console.groupEnd();
        return;
    }

    console.group('📂 File Selection');
    console.log('Raw File Object:', selectedFile);
    
    // Validate file type
    const allowedTypes = [
        'audio/mpeg',   // MP3
        'audio/wav',    // WAV
        'audio/mp3',    // Alternative MP3 mime type
        'audio/x-wav',  // Alternative WAV mime type
        'audio/ogg',    // OGG Audio
        'audio/webm',   // WebM Audio
        'audio/x-m4a',  // M4A Audio
        'audio/aac'     // AAC Audio
    ];

    if (!allowedTypes.includes(selectedFile.type)) {
        console.warn('❌ Invalid File Type');
        console.warn('File Type Received:', selectedFile.type);
        alert('אנא בחר קובץ אודיו תקף (MP3, WAV, OGG או פורמטים נוספים)');
        fileInput.value = ''; // Clear the input
        console.groupEnd();
        return;
    }
    
    // Validate file size (max 10MB)
    const maxSize = 10 * 1024 * 1024; // 10MB
    if (selectedFile.size > maxSize) {
        console.warn('❌ File Too Large');
        alert('הקובץ גדול מדי. גודל מרבי: 10MB');
        fileInput.value = ''; // Clear the input
        console.groupEnd();
        return;
    }
    
    console.log('✅ File Selected Successfully');
    console.groupEnd();

    console.group('🎙️ Transcription Attempt');
    console.log('Selected File:', selectedFile);

    // Create FormData with detailed logging
    const formData = new FormData();
    formData.append('file', selectedFile);

    console.log('FormData Contents:');
    for (let [key, value] of formData.entries()) {
        console.log(`  Key: ${key}, Value:`, value);
    }

    try {
        console.log('Sending Request to:', TRANSCRIPTION_ENDPOINT);
        
        transcribeBtn.disabled = true;
        loadingAnimation.style.display = 'inline-block';
        transcriptionText.textContent = '';

        const fetchOptions = {
            method: 'POST',
            body: formData
        };

        console.log('Fetch Options:', fetchOptions);

        const response = await fetch(TRANSCRIPTION_ENDPOINT, fetchOptions);

        console.log('Response Details:', {
            status: response.status,
            statusText: response.statusText,
            headers: Object.fromEntries(response.headers.entries())
        });

        if (!response.ok) {
            const errorText = await response.text();
            console.error('Error Response:', errorText);
            throw new Error(`שגיאה בביצוע התמלול: ${errorText}`);
        }

        const data = await response.json();
        console.log('Transcription Response:', data);
        
        transcriptionText.textContent = data.transcription || 'לא התקבל טקסט';
        console.log('✅ Transcription Successful');
    } catch (error) {
        console.error('❌ Full Transcription Error:', error);
        transcriptionText.textContent = `שגיאה: ${error.message}`;
    } finally {
        transcribeBtn.disabled = false;
        loadingAnimation.style.display = 'none';
        console.groupEnd();
    }
});