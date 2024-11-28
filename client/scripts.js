let dropArea = document.getElementById('drop-area');
let transcriptionText = document.getElementById('transcription-text');
let selectedFileDiv = document.getElementById('selected-file');
let transcribeBtn = document.getElementById('transcribe-btn');
let loadingAnimation = document.getElementById('loading-animation');
let selectedFile = null;

// Dynamic transcription endpoint using current domain
const TRANSCRIPTION_ENDPOINT = `${window.location.origin}/transcribe`;
console.log('Transcription Endpoint:', TRANSCRIPTION_ENDPOINT);

['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    dropArea.addEventListener(eventName, preventDefaults, false);
});

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

['dragenter', 'dragover'].forEach(eventName => {
    dropArea.addEventListener(eventName, highlight, false);
});

['dragleave', 'drop'].forEach(eventName => {
    dropArea.addEventListener(eventName, unhighlight, false);
});

function highlight(e) {
    dropArea.classList.add('highlight');
}

function unhighlight(e) {
    dropArea.classList.remove('highlight');
}

dropArea.addEventListener('drop', handleDrop, false);

function handleDrop(e) {
    let dt = e.dataTransfer;
    let files = dt.files;
    handleFiles(files);
}

function handleFiles(files) {
    if (files.length > 0) {
        selectedFile = files[0];
        selectedFileDiv.textContent = `קובץ נבחר: ${selectedFile.name}`;
        transcribeBtn.disabled = false;
    }
}

transcribeBtn.addEventListener('click', async () => {
    if (selectedFile) {
        try {
            const formData = new FormData();
            formData.append('file', selectedFile);

            console.log('Sending request to:', TRANSCRIPTION_ENDPOINT);
            console.log('File:', selectedFile.name);

            transcribeBtn.style.display = 'none';
            loadingAnimation.style.display = 'inline-block';

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
            transcribeBtn.style.display = 'block';
            loadingAnimation.style.display = 'none';
        }
    }
});

document.getElementById('fileElem').addEventListener('change', function(e) {
    handleFiles(this.files);
});