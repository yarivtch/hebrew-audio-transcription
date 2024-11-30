# Standard library imports
import os
import uuid
import logging
import traceback
import io
import wave

# Set OpenMP environment variable to avoid conflicts
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

# Third-party library imports
import numpy as np
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from scipy import signal

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'transcription.log')),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, static_folder='../client', static_url_path='/')
CORS(app)

# Global model initialization with lazy loading
_model = None

def get_whisper_model():
    global _model
    if _model is None:
        try:
            from faster_whisper import WhisperModel
            _model = WhisperModel('ivrit-ai/faster-whisper-v2-d4', device="cpu", compute_type="int8")
            logger.info("Model loaded successfully")
        except Exception as e:
            logger.error(f"Model loading error: {e}")
            _model = None
            
    return _model

def read_wav_file(file_buffer):
    """Read WAV file and return audio data as float32 numpy array."""
    with wave.open(file_buffer, 'rb') as wav_file:
        # Get basic information
        channels = wav_file.getnchannels()
        sample_width = wav_file.getsampwidth()
        frame_rate = wav_file.getframerate()
        n_frames = wav_file.getnframes()
        
        # Read raw audio data
        raw_data = wav_file.readframes(n_frames)
        
        # Convert to numpy array
        audio_data = np.frombuffer(raw_data, dtype=np.int16)
        
        # Convert to float32 and normalize
        audio_data = audio_data.astype(np.float32)
        audio_data /= 32768.0  # normalize 16-bit audio
        
        # Convert to mono if stereo
        if channels == 2:
            audio_data = audio_data.reshape(-1, 2).mean(axis=1)
        
        # Resample to 16kHz if needed
        if frame_rate != 16000:
            audio_data = signal.resample(audio_data, int(len(audio_data) * 16000 / frame_rate))
        
        return audio_data, channels, frame_rate

@app.route('/transcribe', methods=['POST'])
def transcribe():
    try:
        # Log request details
        logger.info(f"Request Content-Type: {request.content_type}")
        logger.info(f"Files in request: {list(request.files.keys())}")
        logger.info(f"Form data in request: {list(request.form.keys())}")
        
        # Check if file was uploaded
        if 'audio' not in request.files:
            error_details = {
                'error': 'לא סופק קובץ אודיו',
                'details': {
                    'content_type': request.content_type,
                    'files_keys': list(request.files.keys()),
                    'form_keys': list(request.form.keys())
                }
            }
            logger.error(f"File upload error: {error_details}")
            return jsonify(error_details), 400
        
        audio_file = request.files['audio']
        if not audio_file:
            return jsonify({'error': 'קובץ אודיו ריק'}), 400
        
        # Read file content into memory
        audio_content = audio_file.read()
        audio_buffer = io.BytesIO(audio_content)
        
        # Log file details
        logger.info(f"File Details:")
        logger.info(f"  Content Type: {audio_file.content_type}")
        logger.info(f"  Filename: {audio_file.filename}")
        logger.info(f"  Size: {len(audio_content)} bytes")
        
        try:
            # Read WAV file
            audio_data, channels, frame_rate = read_wav_file(audio_buffer)
            
            # Log audio properties
            logger.info(f"Audio Properties:")
            logger.info(f"  Sample Rate: {frame_rate} Hz")
            logger.info(f"  Channels: {channels}")
            logger.info(f"  Data Shape: {audio_data.shape}")
            
            # Get transcription model
            model = get_whisper_model()
            if not model:
                return jsonify({'error': 'מודל התמלול לא נטען בהצלחה'}), 500
            
            # Perform transcription
            segments, info = model.transcribe(
                audio_data,
                language='he',  # Specify Hebrew
                beam_size=5,    # Improved accuracy
                task='transcribe'
            )
            
            # Process segments
            transcription = ""
            for segment in segments:
                transcription += segment.text + " "
            
            # Log transcription results
            logger.info(f"Transcription completed. Length: {len(transcription)} characters")
            
            return jsonify({
                'transcription': transcription.strip(),
                'language': 'he',
                'confidence': 0.85
            })
            
        except Exception as e:
            logger.error(f"Audio Processing Error: {str(e)}")
            logger.error(traceback.format_exc())
            return jsonify({'error': f'שגיאה בעיבוד קובץ האודיו: {str(e)}'}), 400
            
    except Exception as e:
        logger.error(f"Unexpected Error: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/')
def serve_client():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5002))
    app.run(host='0.0.0.0', port=port, debug=False)