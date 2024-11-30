document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const fileInput = document.getElementById('fileElem');
    const selectedFileDiv = document.getElementById('selected-file');
    const transcribeBtn = document.getElementById('transcribe-btn');
    const chatMessages = document.getElementById('chat-messages');
    const loadingAnimation = document.getElementById('loading-animation');

    let selectedFile = null;
    let audioContext = null;

    // File input change handler
    fileInput.addEventListener('change', function() {
        if (this.files && this.files.length > 0) {
            const file = this.files[0];
            selectedFile = file;
            
            // Create user message for file selection
            const messageDiv = document.createElement('div');
            messageDiv.classList.add('message', 'user-message');
            messageDiv.textContent = `נבחר קובץ: ${file.name}`;
            chatMessages.appendChild(messageDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
            
            // Enable transcribe button
            transcribeBtn.disabled = false;
        }
    });

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
        return new File([wavData], 'audio.wav', {
            type: 'audio/wav'
        });
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

    // Transcribe button click handler
    transcribeBtn.addEventListener('click', async () => {
        if (!selectedFile) return;

        try {
            transcribeBtn.disabled = true;
            loadingAnimation.style.display = 'block';

            // Add system message for processing
            const processingDiv = document.createElement('div');
            processingDiv.classList.add('message', 'system-message');
            processingDiv.textContent = 'מעבד את הקובץ...';
            chatMessages.appendChild(processingDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;

            // Convert audio to WAV format
            const wavFile = await convertToWav(selectedFile);

            // Create form data
            const formData = new FormData();
            formData.append('file', wavFile);

            // Send to server
            const response = await fetch('/transcribe', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error('שגיאה בתמלול');
            }

            const data = await response.json();

            // Remove processing message
            chatMessages.removeChild(processingDiv);

            // Add transcription to chat
            const messageDiv = document.createElement('div');
            messageDiv.classList.add('message', 'transcription-message');
            messageDiv.textContent = data.transcription;
            chatMessages.appendChild(messageDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;

        } catch (error) {
            console.error('Error:', error);
            const errorDiv = document.createElement('div');
            errorDiv.classList.add('message', 'system-message');
            errorDiv.textContent = `שגיאה: ${error.message}`;
            chatMessages.appendChild(errorDiv);
        } finally {
            transcribeBtn.disabled = false;
            loadingAnimation.style.display = 'none';
        }
    });
});