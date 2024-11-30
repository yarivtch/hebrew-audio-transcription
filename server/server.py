# Standard library imports
import os
import uuid
import logging
import traceback
import io
import wave
import functools
import time
import threading
import queue
import sys

# Set OpenMP environment variable to avoid conflicts
if 'KMP_DUPLICATE_LIB_OK' not in os.environ:
    os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
    logger = logging.getLogger(__name__)
    logger.info("Set KMP_DUPLICATE_LIB_OK to TRUE")
else:
    logger = logging.getLogger(__name__)
    logger.info(f"KMP_DUPLICATE_LIB_OK already set to: {os.environ['KMP_DUPLICATE_LIB_OK']}")

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
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
client_dir = os.path.join(base_dir, 'client')
app = Flask(__name__, static_folder=client_dir, static_url_path='/')
CORS(app)

# Global model cache with timeout mechanism
class ModelCache:
    def __init__(self, timeout=1800):  # 30 minutes default timeout
        self._model = None
        self._lock = threading.Lock()
        self._last_loaded_time = 0
        self._timeout = timeout
        self._download_queue = queue.Queue()
        self._cache_dir = os.path.join('/tmp', 'whisper_model_cache')

    def get_model(self):
        with self._lock:
            current_time = time.time()
            
            # Log current model status
            logger.info(f"Model cache status:")
            logger.info(f"  Current model: {'Exists' if self._model is not None else 'None'}")
            logger.info(f"  Last loaded: {time.ctime(self._last_loaded_time)}")
            logger.info(f"  Time since last load: {current_time - self._last_loaded_time:.2f} seconds")
            logger.info(f"  Timeout: {self._timeout} seconds")
            
            # Check if model exists and is not expired
            if (self._model is not None and 
                current_time - self._last_loaded_time < self._timeout):
                logger.info("Using existing cached model")
                return self._model
            
            # Reset model and last loaded time
            self._model = None
            self._last_loaded_time = 0
            
            try:
                # Ensure WhisperModel is imported here
                from faster_whisper import WhisperModel
                
                logger.info("Attempting to load Whisper model")
                logger.info(f"  Cache directory: {self._cache_dir}")
                
                # Ensure cache directory exists
                os.makedirs(self._cache_dir, exist_ok=True)
                
                start_time = time.time()
                
                # Log system details
                logger.info("System details:")
                logger.info(f"  Python version: {sys.version}")
                logger.info(f"  Platform: {sys.platform}")
                logger.info(f"  CPU cores: {os.cpu_count()}")
                
                model = WhisperModel(
                    'ivrit-ai/faster-whisper-v2-d4', 
                    device="cpu", 
                    compute_type="int8",
                    download_root=self._cache_dir
                )
                
                end_time = time.time()
                load_duration = end_time - start_time
                
                # Detailed logging about model load
                logger.info("Model load details:")
                logger.info(f"  Load duration: {load_duration:.2f} seconds")
                logger.info(f"  Cache directory used: {self._cache_dir}")
                
                self._model = model
                self._last_loaded_time = current_time
                
                return self._model
            
            except Exception as e:
                logger.error(" Model loading FAILED:")
                logger.error(f"  Error: {e}")
                logger.error(f"  Traceback: {traceback.format_exc()}")
                
                # Log directory contents for debugging
                try:
                    logger.info("Cache directory contents:")
                    for root, dirs, files in os.walk(self._cache_dir):
                        for file in files:
                            logger.info(f"  - {os.path.join(root, file)}")
                except Exception as dir_error:
                    logger.error(f"Could not list cache directory: {dir_error}")
                
                return None

# Initialize global model cache
_model_cache = ModelCache()

def get_whisper_model():
    return _model_cache.get_model()

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
        # Log incoming request details
        logger.info(f"Transcription request received. Content type: {request.content_type}")
        logger.info(f"Request headers: {dict(request.headers)}")
        
        # Check if file is present
        if 'file' not in request.files:
            logger.error("No file part in the request")
            return jsonify({'error': 'לא נשלח קובץ אודיו'}), 400
        
        audio_file = request.files['file']
        
        # Log file details
        logger.info(f"Received file: {audio_file.filename}")
        logger.info(f"File content type: {audio_file.content_type}")
        
        # Validate file
        if audio_file.filename == '':
            logger.error("No selected file")
            return jsonify({'error': 'לא נבחר קובץ'}), 400
        
        try:
            # Read audio file
            audio_buffer = io.BytesIO(audio_file.read())
            audio_data, channels, frame_rate = read_wav_file(audio_buffer)
            
            # Log audio data details
            logger.info(f"Audio data shape: {audio_data.shape}")
            logger.info(f"Audio data dtype: {audio_data.dtype}")
            logger.info(f"Audio data min/max: {audio_data.min()}, {audio_data.max()}")
            
            # Load model
            model = get_whisper_model()
            if model is None:
                logger.error("Failed to load Whisper model")
                return jsonify({'error': 'שגיאה בטעינת מודל התמלול'}), 500
            
            # Perform transcription
            try:
                segments, info = model.transcribe(
                    audio_data, 
                    language='he', 
                    beam_size=5, 
                    no_speech_threshold=0.6
                )
                
                # Combine segments
                transcription = ' '.join(segment.text for segment in segments)
                
                logger.info(f"Transcription completed. Length: {len(transcription)} characters")
                
                # Return JSON response
                return jsonify({
                    'transcription': transcription.strip(),
                    'language': 'he',
                    'confidence': float(info.language_probability)
                })
            
            except Exception as transcribe_error:
                logger.error(f"Transcription error: {transcribe_error}")
                return jsonify({
                    'error': f'שגיאה בביצוע התמלול: {str(transcribe_error)}',
                    'details': str(transcribe_error)
                }), 500
        
        except Exception as file_error:
            logger.error(f"File processing error: {file_error}")
            return jsonify({
                'error': f'שגיאה בעיבוד הקובץ: {str(file_error)}',
                'details': str(file_error)
            }), 400
    
    except Exception as general_error:
        logger.error(f"General transcription error: {general_error}")
        return jsonify({
            'error': f'שגיאה כללית: {str(general_error)}',
            'details': str(general_error)
        }), 500

@app.route('/debug-static')
def debug_static():
    try:
        logger.info(f"Static folder: {app.static_folder}")
        logger.info(f"Static files: {os.listdir(app.static_folder)}")
        return jsonify({
            'static_folder': app.static_folder,
            'static_files': os.listdir(app.static_folder)
        })
    except Exception as e:
        logger.error(f"Debug static error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.errorhandler(Exception)
def handle_global_error(e):
    logger.error(f"Global error handler caught: {str(e)}")
    logger.error(traceback.format_exc())
    return jsonify({
        'error': 'שגיאה לא צפויה במערכת',
        'details': str(e)
    }), 500

@app.route('/')
def serve_client():
    try:
        logger.info(f"Serving index.html from: {app.static_folder}")
        return send_from_directory(app.static_folder, 'index.html')
    except Exception as e:
        logger.error(f"Error serving index.html: {str(e)}")
        return jsonify({'error': f'שגיאה בטעינת דף ראשי: {str(e)}'}), 500

@app.route('/<path:path>')
def serve_static(path):
    try:
        logger.info(f"Requested static file: {path}")
        full_path = os.path.join(app.static_folder, path)
        logger.info(f"Full path: {full_path}")
        if not os.path.exists(full_path):
            logger.error(f"File not found: {full_path}")
            return jsonify({'error': f'קובץ לא נמצא: {path}'}), 404
        return send_from_directory(app.static_folder, path)
    except Exception as e:
        logger.error(f"Error serving static file {path}: {str(e)}")
        return jsonify({'error': f'שגיאה בטעינת קובץ: {str(e)}'}), 500

def preload_model():
    """
    טעינת המודל מראש כדי למנוע עיכוב בבקשה הראשונה
    """
    try:
        logger.info(" Starting Whisper model preload...")
        start_time = time.time()
        
        model = _model_cache.get_model()
        
        end_time = time.time()
        
        if model:
            logger.info(" Whisper model preloaded successfully")
            logger.info(f"  Total preload time: {end_time - start_time:.2f} seconds")
        else:
            logger.error(" Failed to preload Whisper model")
    except Exception as e:
        logger.error(f" Preload process failed: {e}")
        logger.error(traceback.format_exc())

preload_model()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5002))
    app.run(host='0.0.0.0', port=port, debug=False)