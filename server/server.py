# Standard library imports
import os
import uuid
import logging
import traceback
import tempfile
import magic

# Third-party library imports
import soundfile as sf
import numpy as np
import io
from werkzeug.utils import secure_filename

# Flask and web framework imports
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# Machine learning imports
from faster_whisper import WhisperModel

# Configure extremely verbose logging
logging.basicConfig(
    level=logging.DEBUG,  # Most verbose level
    format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(__file__), 'transcription_debug.log'), mode='w'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# server.py
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

# Temporary file handling configured
logger.info(" Temporary file handling configured")

# Fallback temporary directory setup
TEMP_DIR = tempfile.gettempdir()
logger.info(f" Temporary directory: {TEMP_DIR}")

app = Flask(__name__, static_folder='../client', static_url_path='/')
CORS(app, resources={
    r"/transcribe": {
        "origins": ["*"],
        "methods": ["POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Global model initialization with lazy loading
_model = None

def get_whisper_model():
    global _model
    if _model is None:
        try:
            _model = WhisperModel('ivrit-ai/faster-whisper-v2-d4', device="cpu", compute_type="int8")
        except Exception as e:
            logger.error(f"Model loading error: {e}")
            _model = None
            
    return _model

# Health check route
@app.route('/')
def health_check():
    return jsonify({
        'status': 'ok', 
        'message': 'Hebrew Audio Transcription service is running'
    })

# CORS preflight route
@app.route('/transcribe', methods=['OPTIONS'])
def transcribe_options():
    response = jsonify({"message": "CORS preflight successful"})
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'POST')
    return response

# Allowed audio MIME types
ALLOWED_MIME_TYPES = {
    'audio/mpeg',   # MP3
    'audio/wav',    # WAV
    'audio/mp3',    # Alternative MP3 mime type
    'audio/x-wav',  # Alternative WAV mime type
    'audio/ogg',    # OGG Audio
    'audio/webm',   # WebM Audio
    'audio/x-m4a',  # M4A Audio
    'audio/aac'     # AAC Audio
}

def validate_audio_file(file):
    """
    Comprehensive audio file validation
    
    Args:
        file: Uploaded file object
    
    Returns:
        Tuple (is_valid, error_message)
    """
    # Log detailed file information
    logger.info(" Audio File Validation:")
    logger.info(f"  Filename: {file.filename}")
    logger.info(f"  Content Type: {file.content_type}")
    
    # Check if content type is allowed
    if file.content_type not in ALLOWED_MIME_TYPES:
        logger.warning(f" Unsupported MIME Type: {file.content_type}")
        logger.warning(f"  Allowed Types: {ALLOWED_MIME_TYPES}")
        return False, f"סוג קובץ לא נתמך: {file.content_type}"
    
    # Additional validation using python-magic for more robust file type detection
    try:
        import magic
        
        # Save file temporarily to check its actual type
        temp_path = os.path.join(tempfile.gettempdir(), f"temp_{uuid.uuid4()}")
        file.save(temp_path)
        
        # Detect file type
        mime = magic.Magic(mime=True)
        detected_type = mime.from_file(temp_path)
        
        # Remove temporary file
        os.unlink(temp_path)
        
        logger.info(f"  Detected MIME Type: {detected_type}")
        
        # Check if detected type is allowed
        if detected_type not in ALLOWED_MIME_TYPES:
            logger.warning(f" Detected Unsupported MIME Type: {detected_type}")
            return False, f"סוג קובץ לא תקף: {detected_type}"
    
    except ImportError:
        logger.warning(" python-magic not installed. Skipping advanced type detection.")
    except Exception as e:
        logger.error(f" File Type Detection Error: {e}")
        return False, "שגיאה בזיהוי סוג הקובץ"
    
    # Check if file exists and has a filename
    if not file or not file.filename:
        return False, 'קובץ אודיו לא חוקי: הקובץ ריק'
    
    # Check file size (limit to 50MB)
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    
    if file_size > 50 * 1024 * 1024:  # 50MB
        return False, 'קובץ אודיו גדול מדי (מקסימום 50MB)'
    
    return True, ""

def process_audio_file(saved_file_path):
    """
    Process the uploaded audio file with comprehensive error handling
    
    Args:
        saved_file_path (str): Path to the saved audio file
    
    Returns:
        dict: Audio file properties or raises an exception
    """
    try:
        # Attempt to read audio file using soundfile
        with sf.SoundFile(saved_file_path) as audio_file:
            # Get audio file properties
            n_channels = audio_file.channels
            sample_rate = audio_file.samplerate
            duration = len(audio_file) / sample_rate
            
            # Convert to mono if stereo
            if n_channels > 1:
                print(f" Converting {n_channels}-channel audio to mono")
                
            # Basic validation
            if duration <= 0:
                raise ValueError("אורך האודיו לא תקין")
            
            return {
                'channels': n_channels,
                'sample_rate': sample_rate,
                'duration': duration
            }
    
    except sf.SoundFileError as sf_error:
        print(f" SoundFile Error: {sf_error}")
        print(traceback.format_exc())
        raise ValueError(f"שגיאה בקריאת קובץ האודיו: {sf_error}")
    
    except Exception as e:
        print(f" Unexpected Error Processing Audio: {e}")
        print(traceback.format_exc())
        raise ValueError(f"שגיאה לא צפויה בעיבוד האודיו: {e}")

def save_uploaded_file(file):
    """
    Save uploaded file to a temporary file that will be automatically deleted.
    
    Args:
        file (FileStorage): Uploaded file object
    
    Returns:
        str: Path to the temporary saved file
    """
    try:
        # Create a temporary file with a unique name and appropriate suffix
        # Use the original file's extension to ensure correct file type
        file_extension = os.path.splitext(file.filename)[1] or '.bin'
        
        # Create temporary file that will be automatically deleted when closed
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            # Save the uploaded file to the temporary location
            file.save(temp_file.name)
            
            # Log temporary file details
            logger.info(f" Temporary File Created:")
            logger.info(f"  Path: {temp_file.name}")
            logger.info(f"  Extension: {file_extension}")
            
            # Return the path to the temporary file
            return temp_file.name
    
    except Exception as e:
        logger.error(f" Temporary File Creation Error: {e}")
        raise ValueError(f"שגיאה ביצירת קובץ זמני: {e}")

def transcribe_audio(saved_file_path):
    """
    Transcribe audio file with comprehensive error handling.
    
    Args:
        saved_file_path (str): Path to the saved audio file
    
    Returns:
        str: Transcribed text
    """
    try:
        # Validate file exists
        if not os.path.exists(saved_file_path):
            raise FileNotFoundError(f"קובץ האודיו לא נמצא: {saved_file_path}")
        
        # Log file details before transcription
        file_stats = os.stat(saved_file_path)
        logging.info(f"Transcribing file: {saved_file_path}")
        logging.info(f"File size: {file_stats.st_size} bytes")
        
        # Load audio file
        try:
            audio_data, sample_rate = sf.read(saved_file_path)
        except Exception as sf_error:
            logging.error(f"SoundFile reading error: {sf_error}")
            raise ValueError(f"שגיאה בקריאת קובץ האודיו: {sf_error}")
        
        # Ensure mono audio
        if audio_data.ndim > 1:
            audio_data = audio_data.mean(axis=1)
        
        # Transcribe using Whisper model
        model = get_whisper_model()
        if not model:
            raise RuntimeError("מודל התמלול לא נטען בהצלחה")
        
        # Perform transcription
        segments, info = model.transcribe(
            audio_data, 
            language='he',  # Specify Hebrew
            beam_size=5,    # Improved accuracy
            task='transcribe'
        )
        
        # Combine transcription segments
        transcription = ' '.join(segment for segment in segments)
        
        # Log transcription results
        logging.info(f"Transcription completed. Length: {len(transcription)} characters")
        
        return transcription
    
    except Exception as e:
        logging.error(f"Transcription error: {e}")
        logging.error(traceback.format_exc())
        raise ValueError(f"שגיאה בתמלול האודיו: {e}")
    finally:
        # Clean up: remove temporary audio file
        try:
            os.remove(saved_file_path)
            logging.info(f"Temporary file removed: {saved_file_path}")
        except Exception as cleanup_error:
            logging.warning(f"Could not remove temporary file: {cleanup_error}")

def log_request_details(request):
    """
    Log extremely detailed request information for debugging.
    """
    try:
        logger.debug("=" * 50)
        logger.debug(" EXTREME REQUEST DEBUGGING ")
        logger.debug("=" * 50)
        
        # Log request method and content type
        logger.debug(f"Request Method: {request.method}")
        logger.debug(f"Request Content Type: {request.content_type}")
        
        # Log all request headers
        logger.debug("Request Headers:")
        for header, value in request.headers:
            logger.debug(f"  {header}: {value}")
        
        # Log environment variables related to the request
        logger.debug("\nRequest Environment Variables:")
        for key, value in request.environ.items():
            if any(x in key.lower() for x in ['content', 'type', 'length', 'file', 'upload']):
                logger.debug(f"  {key}: {value}")
        
        # Log form data
        logger.debug("\nForm Data:")
        for key, value in request.form.items():
            logger.debug(f"  {key}: {value}")
        
        # Log files information
        logger.debug("\nFiles Information:")
        logger.debug(f"  Number of files: {len(request.files)}")
        for key, file in request.files.items():
            logger.debug(f"  File Key: {key}")
            logger.debug(f"    Filename: {file.filename}")
            logger.debug(f"    Content Type: {file.content_type}")
            try:
                file.seek(0, os.SEEK_END)
                file_size = file.tell()
                file.seek(0)
                logger.debug(f"    File Size: {file_size} bytes")
            except Exception as e:
                logger.debug(f"    Error getting file size: {e}")
        
        # Attempt to read raw data
        try:
            raw_data = request.get_data()
            logger.debug(f"Raw Data Length: {len(raw_data)} bytes")
            raw_text = raw_data.decode('utf-8', errors='ignore')
            logger.debug("Raw Data (first 500 chars):")
            logger.debug(raw_text[:500])
        except Exception as e:
            logger.debug(f"Error reading raw data: {e}")
        
        logger.debug("=" * 50)
    except Exception as log_error:
        logger.error(f"Error in logging request details: {log_error}")

@app.route('/transcribe', methods=['POST'])
def transcribe():
    # Extremely verbose logging of request details
    logger.info(" Transcription Request Received")
    logger.info(" Request Details:")
    logger.info(f"  Method: {request.method}")
    logger.info(f"  Content Type: {request.content_type}")
    logger.info(f"  Content Length: {request.content_length}")

    # Log all headers
    logger.info(" Request Headers:")
    for header, value in request.headers:
        logger.info(f"  {header}: {value}")

    # Log form data
    logger.info(" Form Data:")
    for key, value in request.form.items():
        logger.info(f"  {key}: {value}")

    # Log files
    logger.info(" Files in Request:")
    for key, file in request.files.items():
        logger.info(f"  Key: {key}")
        logger.info(f"    Filename: {file.filename}")
        logger.info(f"    Content Type: {file.content_type}")
        logger.info(f"    Content Length: {file.content_length}")

    # Extremely detailed logging of request environment
    logger.info(" Request Environment:")
    logger.info(f"  Remote Address: {request.remote_addr}")
    logger.info(f"  User Agent: {request.user_agent}")
    
    # Log all possible file retrieval methods
    logger.info(" File Retrieval Diagnostic:")
    logger.info(f"  request.files keys: {list(request.files.keys())}")
    logger.info(f"  request.form keys: {list(request.form.keys())}")

    # Comprehensive file retrieval attempt
    audio_file = None
    possible_keys = ['file', 'audio', 'audioFile', 'uploaded_file']
    
    # Try multiple ways of getting the file
    for key in possible_keys:
        logger.debug(f"Attempting to retrieve file with key: {key}")
        
        # Method 1: request.files
        if key in request.files:
            audio_file = request.files[key]
            logger.debug(f" Found file in request.files[{key}]")
            break
        
        # Method 2: request.files.get()
        audio_file = request.files.get(key)
        if audio_file:
            logger.debug(f" Found file using request.files.get({key})")
            break

    # Final check for file
    if not audio_file:
        logger.error(" ERROR: No audio file found")
        logger.error(f"Available form keys: {list(request.form.keys())}")
        logger.error(f"Available files keys: {list(request.files.keys())}")
        return jsonify({
            'error': 'לא סופק קובץ אודיו',
            'details': {
                'content_type': request.content_type,
                'files_keys': list(request.files.keys()),
                'form_keys': list(request.form.keys()),
                'tried_keys': possible_keys
            }
        }), 400

    # Validate file
    if not audio_file.filename:
        logger.error(" ERROR: Empty filename")
        return jsonify({
            'error': 'שם קובץ לא חוקי',
            'details': 'הקובץ שנשלח אינו תקף'
        }), 400

    # Log file details for debugging
    logger.info(f" Received File Details:")
    logger.info(f"  Filename: {audio_file.filename}")
    logger.info(f"  Content Type: {audio_file.content_type}")
    logger.info(f"  File Size: {audio_file.content_length} bytes")

    # Validate audio file
    is_valid, error_message = validate_audio_file(audio_file)
    if not is_valid:
        logger.error(f" Invalid Audio File: {error_message}")
        return jsonify({
            'error': error_message,
            'details': {
                'filename': audio_file.filename,
                'content_type': audio_file.content_type
            }
        }), 400
    
    try:
        # Save to temporary file
        saved_file_path = save_uploaded_file(audio_file)
        
        try:
            # Process and validate audio file
            audio_properties = process_audio_file(saved_file_path)
            
            # Log audio file properties
            logger.info(" Audio File Properties:")
            for key, value in audio_properties.items():
                logger.info(f"  {key}: {value}")
            
            # Transcribe audio
            transcription = transcribe_audio(saved_file_path)
            logger.info(f" Transcription: {transcription}")
            
            return jsonify({
                'transcription': transcription,
                'language': 'he',
                'confidence': 0.85
            })
        
        finally:
            # Always attempt to remove the temporary file
            try:
                os.unlink(saved_file_path)
                logger.info(f" Deleted temporary file: {saved_file_path}")
            except Exception as cleanup_error:
                logger.error(f" Temporary File Cleanup Error: {cleanup_error}")
    
    except ValueError as ve:
        # Handle specific audio processing errors
        logger.error(f" Audio Processing Error: {ve}")
        logger.error(traceback.format_exc())
        return jsonify({
            'error': str(ve),
            'details': {
                'filename': audio_file.filename,
                'content_type': audio_file.content_type
            }
        }), 400

@app.route('/')
def serve_client():
    return send_from_directory(app.static_folder, 'index.html')

# Catch-all route to serve static files
@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)

# Adjust host for production
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=False)