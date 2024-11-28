document.addEventListener('DOMContentLoaded', function() {
    const dropzone = document.getElementById('dropzone');
    const fileInput = document.getElementById('fileInput');
    const transcribeBtn = document.getElementById('transcribeBtn');
    const loading = document.getElementById('loading');
    const result = document.getElementById('result');

    // טיפול בגרירת קבצים
    dropzone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropzone.classList.add('drag-over');
    });

    dropzone.addEventListener('dragleave', () => {
        dropzone.classList.remove('drag-over');
    });

    dropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropzone.classList.remove('drag-over');
        handleFiles(e.dataTransfer.files);
    });

    // טיפול בבחירת קבצים
    dropzone.addEventListener('click', () => {
        fileInput.click();
    });

    fileInput.addEventListener('change', (e) => {
        handleFiles(e.target.files);
    });

    function handleFiles(files) {
        if (files.length > 0) {
            const file = files[0];
            if (file.type.startsWith('audio/')) {
                dropzone.textContent = `נבחר: ${file.name}`;
                transcribeBtn.style.display = 'block';
            } else {
                alert('אנא בחר קובץ אודיו');
            }
        }
    }

    transcribeBtn.addEventListener('click', async () => {
        const file = fileInput.files[0];
        if (!file) return;

        const formData = new FormData();
        formData.append('audio', file);

        loading.style.display = 'block';
        transcribeBtn.disabled = true;
        result.style.display = 'none';

        try {
            const response = await fetch('http://localhost:5000/transcribe', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.success) {
                result.textContent = data.transcription;
                result.style.display = 'block';
            } else {
                throw new Error(data.error);
            }
        } catch (error) {
            alert('שגיאה בתמלול: ' + error.message);
        } finally {
            loading.style.display = 'none';
            transcribeBtn.disabled = false;
        }
    });
});