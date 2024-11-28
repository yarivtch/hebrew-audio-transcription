let dropArea = document.getElementById('drop-area');
let transcriptionText = document.getElementById('transcription-text');
let selectedFileDiv = document.getElementById('selected-file');
let transcribeBtn = document.getElementById('transcribe-btn');
let loadingAnimation = document.getElementById('loading-animation');
let selectedFile = null;

// Dynamic transcription endpoint using current domain
const TRANSCRIPTION_ENDPOINT = `${window.location.origin}/transcribe`;

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

            transcribeBtn.style.display = 'none';
            loadingAnimation.style.display = 'inline-block';

            const response = await fetch(TRANSCRIPTION_ENDPOINT, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error('שגיאה בביצוע התמלול');
            }

            const data = await response.json();
            transcriptionText.textContent = data.transcription || 'לא התקבל טקסט';
        } catch (error) {
            console.error('Error:', error);
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