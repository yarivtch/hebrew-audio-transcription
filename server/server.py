# server.py
from flask import Flask, request, jsonify, send_from_directory
import os
import uuid
import logging
from faster_whisper import WhisperModel
from flask_cors import CORS
import magic
import traceback
import tempfile
import soundfile as sf
import numpy as np
import io

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Uploads directory configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOADS_DIR = os.path.join(BASE_DIR, '..', 'uploads')
os.makedirs(UPLOADS_DIR, exist_ok=True)

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
    'audio/x-wav',  # Alternative WAV
    'audio/mp4',    # M4A
    'audio/ogg',    # OGG
    'audio/webm'    # WebM audio
}

def validate_audio_file(file):
    """
    Comprehensive audio file validation
    
    Args:
        file: Uploaded file object
    
    Returns:
        Tuple (is_valid, error_message)
    """
    # Check if file exists and has a filename
    if not file or not file.filename:
        return False, 'קובץ אודיו לא חוקי: הקובץ ריק'
    
    # Check file size (limit to 50MB)
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    
    if file_size > 50 * 1024 * 1024:  # 50MB
        return False, 'קובץ אודיו גדול מדי (מקסימום 50MB)'
    
    # Detect MIME type
    try:
        mime = magic.Magic(mime=True)
        mime_type = mime.from_buffer(file.read(2048))
        file.seek(0)  # Reset file pointer
        
        print(f"🔍 Detected MIME Type: {mime_type}")
        
        if mime_type not in ALLOWED_MIME_TYPES:
            return False, f'סוג קובץ אודיו לא נתמך: {mime_type}'
        
    except Exception as e:
        print(f"❌ MIME Type Detection Error: {e}")
        return False, 'שגיאה בזיהוי סוג הקובץ'
    
    return True, ''

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
                print(f"🔊 Converting {n_channels}-channel audio to mono")
                
            # Basic validation
            if duration <= 0:
                raise ValueError("אורך האודיו לא תקין")
            
            return {
                'channels': n_channels,
                'sample_rate': sample_rate,
                'duration': duration
            }
    
    except sf.SoundFileError as sf_error:
        print(f"❌ SoundFile Error: {sf_error}")
        print(traceback.format_exc())
        raise ValueError(f"שגיאה בקריאת קובץ האודיו: {sf_error}")
    
    except Exception as e:
        print(f"❌ Unexpected Error Processing Audio: {e}")
        print(traceback.format_exc())
        raise ValueError(f"שגיאה לא צפויה בעיבוד האודיו: {e}")

@app.route('/transcribe', methods=['POST'])
def transcribe():
    try:
        # EXTREME DEBUGGING
        print("\n" + "=" * 50)
        print("🔍 DETAILED REQUEST DEBUGGING 🔍")
        print("=" * 50)
        
        # Print ALL request information
        print(f"Request Method: {request.method}")
        print(f"Request Content Type: {request.content_type}")
        print(f"Request Headers: {dict(request.headers)}")
        
        # Print raw request data
        print("\n📋 Raw Request Data:")
        try:
            raw_data = request.get_data(as_text=True)
            print(f"Raw Data (first 500 chars): {raw_data[:500]}")
        except Exception as e:
            print(f"Error reading raw data: {e}")
        
        # Detailed form and files information
        print("\n📂 Form and Files Information:")
        print(f"Form Keys: {list(request.form.keys())}")
        print(f"Files Keys: {list(request.files.keys())}")
        
        # Detailed form data
        if request.form:
            print("\n📋 Form Data:")
            for key, value in request.form.items():
                print(f"  {key}: {value}")
        
        # Detailed file information
        if request.files:
            print("\n🗂️ File Details:")
            for key, file in request.files.items():
                print(f"File Key: {key}")
                print(f"  Filename: {file.filename}")
                print(f"  Content Type: {file.content_type}")
                try:
                    file.seek(0, os.SEEK_END)
                    file_size = file.tell()
                    file.seek(0)
                    print(f"  File Size: {file_size} bytes")
                except Exception as e:
                    print(f"  Error getting file size: {e}")
        
        # Validate request method
        if request.method != 'POST':
            print("❌ ERROR: Invalid request method")
            return jsonify({
                'error': 'שיטת בקשה לא חוקית',
                'details': f'שיטת בקשה: {request.method}'
            }), 405
        
        # Check if audio file is present
        if not request.files:
            print("❌ ERROR: No files in request")
            return jsonify({
                'error': 'לא סופק קובץ אודיו',
                'details': {
                    'content_type': request.content_type,
                    'files_keys': list(request.files.keys()),
                    'form_keys': list(request.form.keys())
                }
            }), 400
        
        # Attempt to get file with multiple possible keys
        audio_file = None
        possible_keys = ['file', 'audio', 'audioFile']
        for key in possible_keys:
            if key in request.files:
                audio_file = request.files[key]
                print(f"✅ Found file with key: {key}")
                break
        
        if not audio_file:
            print("❌ ERROR: No audio file found with any expected key")
            return jsonify({
                'error': 'לא סופק קובץ אודיו',
                'details': {
                    'tried_keys': possible_keys,
                    'available_keys': list(request.files.keys())
                }
            }), 400
        
        # Additional file validation
        if not audio_file.filename:
            print("❌ ERROR: Empty filename")
            return jsonify({
                'error': 'שם קובץ לא חוקי',
                'details': 'הקובץ שנשלח אינו תקף'
            }), 400

        # Comprehensive file validation
        is_valid, error_message = validate_audio_file(audio_file)
        
        if not is_valid:
            print(f"❌ File Validation Failed: {error_message}")
            return jsonify({
                'error': 'קובץ האודיו אינו תקף',
                'details': error_message
            }), 400
        
        print(f"✅ File Validation Passed: {audio_file.filename}")
        print("=" * 50 + "\n")

        # Extensive logging for debugging
        print("=" * 50)
        print("DEBUG: Transcription Request Received")
        print("=" * 50)
        
        # Detailed request information
        print(f"Request Method: {request.method}")
        print(f"Request Content Type: {request.content_type}")
        print(f"Request Headers: {dict(request.headers)}")
        print(f"Request Form Keys: {list(request.form.keys())}")
        print(f"Request Files Keys: {list(request.files.keys())}")
        
        # Log file details
        print(f"Audio File Details:")
        print(f"  Filename: {audio_file.filename}")
        print(f"  Content Type: {audio_file.content_type}")
        
        try:
            audio_file.seek(0, os.SEEK_END)
            file_size = audio_file.tell()
            audio_file.seek(0)
            print(f"  File Size: {file_size} bytes")
        except Exception as e:
            print(f"  Error getting file size: {e}")
            file_size = 0
        
        # Log all incoming request details
        logger.info(f"Received transcription request")
        logger.info(f"Request headers: {dict(request.headers)}")
        logger.info(f"Request content type: {request.content_type}")
        logger.info(f"Request files: {list(request.files.keys())}")
        logger.info(f"Request form data: {dict(request.form)}")
        
        # Debug: print all request data
        print("DEBUG: All request data:")
        print(f"Headers: {dict(request.headers)}")
        print(f"Content Type: {request.content_type}")
        print(f"Files: {list(request.files.keys())}")
        print(f"Form data: {dict(request.form)}")

        # Generate a unique filename
        original_filename = audio_file.filename or 'unknown'
        unique_filename = f"{uuid.uuid4()}_{original_filename}"
        saved_file_path = os.path.join(UPLOADS_DIR, unique_filename)
        
        # Save the original uploaded file
        audio_file.seek(0)  # Reset file pointer
        audio_file.save(saved_file_path)
        
        try:
            # Process and validate audio file
            audio_properties = process_audio_file(saved_file_path)
            
            # Log audio file properties
            print("🎧 Audio File Properties:")
            for key, value in audio_properties.items():
                print(f"  {key}: {value}")
            
            # Transcribe audio
            try:
                model = get_whisper_model()
                segments, _ = model.transcribe(saved_file_path, language='he', beam_size=15)
                transcription = ' '.join([s.text for s in segments])
            except Exception as transcribe_error:
                logger.error(f"Transcription error: {transcribe_error}", exc_info=True)
                return jsonify({
                    'error': 'שגיאה בתמלול',
                    'details': f'פרטים טכניים: {str(transcribe_error)}'
                }), 500
            
            return jsonify({
                'success': True,
                'transcription': transcription,
                'audio_properties': audio_properties
            })
        
        except ValueError as ve:
            # Handle specific audio processing errors
            return jsonify({
                'error': str(ve),
                'details': {
                    'filename': original_filename
                }
            }), 400
        
        finally:
            # Clean up uploaded file
            if os.path.exists(saved_file_path):
                os.unlink(saved_file_path)
    
    except Exception as e:
        # Catch-all for unexpected errors
        print(f"❌ Unexpected Transcription Error: {e}")
        print(traceback.format_exc())
        
        return jsonify({
            'error': 'שגיאה לא צפויה בתהליך התמלול',
            'details': str(e)
        }), 500

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