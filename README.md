# Hebrew Audio Transcription Web App

## 🎙️ Project Overview
A web application for transcribing Hebrew audio files using machine learning and Flask.

## 🤖 Transcription Model
- **Model**: `ivrit-ai/faster-whisper-v2-d4`
- Specialized Hebrew speech-to-text model
- Powered by Faster Whisper technology
- Optimized for Hebrew language transcription

## 🛠️ Technologies
- Backend: Flask (Python)
- Transcription Model: Faster Whisper (`ivrit-ai/faster-whisper-v2-d4`)
- Frontend: HTML, JavaScript
- Audio Processing: SoundFile
- MIME Type Detection: python-magic

## 📦 Dependencies
- Flask
- Flask-CORS
- Faster Whisper
- SoundFile
- NumPy
- python-magic

## 🚀 Setup and Installation
1. Clone the repository
2. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the server:
   ```bash
   python server/server.py
   ```

## 🔧 Features
- Hebrew audio transcription using `ivrit-ai/faster-whisper-v2-d4`
- Support for multiple audio formats
- Robust error handling
- Simple, user-friendly interface

## 📝 License
[Add your license here]

## 🤝 Contributing
Contributions are welcome! Please read the contributing guidelines before getting started.
