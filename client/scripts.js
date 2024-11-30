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

console.log(' Transcription Endpoint:', TRANSCRIPTION_ENDPOINT);

// DOM Elements
const dropArea = document.getElementById('drop-area');
const fileInput = document.getElementById('fileElem');
const selectedFileDiv = document.getElementById('selected-file');
const transcribeBtn = document.getElementById('transcribe-btn');
const transcriptionText = document.getElementById('transcription-text');
const loadingAnimation = document.getElementById('loading-animation');

let selectedFile = null;

// Prevent default drag behaviors
['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    dropArea.addEventListener(eventName, preventDefaults, false);
    document.body.addEventListener(eventName, preventDefaults, false);
});

// Highlight drop zone when item is dragged over it
['dragenter', 'dragover'].forEach(eventName => {
    dropArea.addEventListener(eventName, highlight, false);
});

['dragleave', 'drop'].forEach(eventName => {
    dropArea.addEventListener(eventName, unhighlight, false);
});

// Handle dropped files
dropArea.addEventListener('drop', handleDrop, false);

function preventDefaults (e) {
    e.preventDefault();
    e.stopPropagation();
}

function highlight(e) {
    dropArea.classList.add('highlight');
}

function unhighlight(e) {
    dropArea.classList.remove('highlight');
}

function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;
    handleFiles(files);
}

function handleFiles(files) {
    if (files.length > 0) {
        selectedFile = files[0];
        selectedFileDiv.textContent = `נבחר: ${selectedFile.name}`;
        transcribeBtn.disabled = false;
    }
}

// File input change handler
fileInput.addEventListener('change', function() {
    handleFiles(this.files);
});

transcribeBtn.addEventListener('click', async () => {
    if (selectedFile) {
        try {
            transcribeBtn.disabled = true;
            loadingAnimation.style.display = 'inline-block';
            transcriptionText.textContent = 'מעבד את הקובץ...';

            const wavFile = await convertToWav(selectedFile);
            await uploadFile(wavFile);
        } catch (error) {
            console.error('Error:', error);
            transcriptionText.textContent = `שגיאה בעיבוד הקובץ: ${error.message}`;
        } finally {
            transcribeBtn.disabled = false;
            loadingAnimation.style.display = 'none';
        }
    }
});

// Audio context for conversion
let audioContext = null;

async function convertToWav(audioFile) {
    // Create audio context if not exists
    if (!audioContext) {
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
    }

    // Read the file
    const arrayBuffer = await audioFile.arrayBuffer();
    
    // Decode the audio data
    const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
    
    // Create offline context for rendering
    const offlineContext = new OfflineAudioContext(
        1, // mono
        audioBuffer.length * (16000 / audioBuffer.sampleRate), // resample to 16kHz
        16000 // target sample rate
    );
    
    // Create buffer source
    const source = offlineContext.createBufferSource();
    source.buffer = audioBuffer;
    source.connect(offlineContext.destination);
    source.start();
    
    // Render audio
    const renderedBuffer = await offlineContext.startRendering();
    
    // Convert to WAV
    const wavData = audioBufferToWav(renderedBuffer);
    
    // Create WAV file
    const wavFile = new File([wavData], 'audio.wav', {
        type: 'audio/wav'
    });
    
    return wavFile;
}

function audioBufferToWav(buffer) {
    const numChannels = 1; // mono
    const sampleRate = buffer.sampleRate;
    const format = 1; // PCM
    const bitDepth = 16;
    
    const bytesPerSample = bitDepth / 8;
    const blockAlign = numChannels * bytesPerSample;
    
    const data = buffer.getChannelData(0);
    const samples = Int16Array.from(data.map(n => n * 32767));
    const buffer_size = samples.length * bytesPerSample;
    
    const wav = new ArrayBuffer(44 + buffer_size);
    const view = new DataView(wav);
    
    // Write WAV header
    writeString(view, 0, 'RIFF');
    view.setUint32(4, 36 + buffer_size, true);
    writeString(view, 8, 'WAVE');
    writeString(view, 12, 'fmt ');
    view.setUint32(16, 16, true);
    view.setUint16(20, format, true);
    view.setUint16(22, numChannels, true);
    view.setUint32(24, sampleRate, true);
    view.setUint32(28, sampleRate * blockAlign, true);
    view.setUint16(32, blockAlign, true);
    view.setUint16(34, bitDepth, true);
    writeString(view, 36, 'data');
    view.setUint32(40, buffer_size, true);
    
    // Write audio data
    for (let i = 0; i < samples.length; i++) {
        view.setInt16(44 + i * bytesPerSample, samples[i], true);
    }
    
    return new Blob([wav], { type: 'audio/wav' });
}

function writeString(view, offset, string) {
    for (let i = 0; i < string.length; i++) {
        view.setUint8(offset + i, string.charCodeAt(i));
    }
}

async function uploadFile(file) {
    const formData = new FormData();
    formData.append('audio', file);

    try {
        const response = await fetch(TRANSCRIPTION_ENDPOINT, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(JSON.stringify(errorData));
        }

        const result = await response.json();
        transcriptionText.textContent = result.transcription;
    } catch (error) {
        console.error('Error response:', error);
        throw new Error(`שגיאה בביצוע התמלול: ${error.message}`);
    }
}