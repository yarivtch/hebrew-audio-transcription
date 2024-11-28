let dropArea = document.getElementById('drop-area');
let transcriptionText = document.getElementById('transcription-text');
let selectedFileDiv = document.getElementById('selected-file');
let transcribeBtn = document.getElementById('transcribe-btn');
let loadingAnimation = document.getElementById('loading-animation');
let selectedFile = null;

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

transcribeBtn.addEventListener('click', () => {
    if (selectedFile) {
        uploadFile(selectedFile);
    }
});

const API_URL = 'http://localhost:5001/transcribe';

function uploadFile(file) {
    console.log(' Uploading File:', {
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

    // מציג את האנימציה ומסתיר את הכפתור
    transcribeBtn.style.display = 'none';
    loadingAnimation.style.display = 'inline-block';

    fetch(API_URL, {
        method: 'POST',
        mode: 'cors', 
        cache: 'no-cache', 
        credentials: 'same-origin', 
        headers: {
        },
        body: formData
    })
    .then(response => {
        console.log('Response Status:', response.status);
        console.log('Response Headers:', Object.fromEntries(response.headers.entries()));
        
        // Check if response is ok (status in 200-299 range)
        if (!response.ok) {
            return response.json().then(errorData => {
                throw new Error(errorData.error || 'שגיאה בלתי צפויה');
            });
        }
        
        return response.json();
    })
    .then(result => {
        if (result.transcription) {
            transcriptionText.textContent = result.transcription;
        } else {
            throw new Error('לא התקבל טקסט תמלול');
        }
    })
    .catch(error => {
        console.error(' Upload Error:', error);
        transcriptionText.textContent = error.message || 'שגיאה בתמלול. אנא נסה שנית.';
    })
    .finally(() => {
        // מחזיר את הכפתור ומסתיר את האנימציה
        transcribeBtn.style.display = 'block';
        loadingAnimation.style.display = 'none';
    });
}

document.getElementById('fileElem').addEventListener('change', function(e) {
    handleFiles(this.files);
});