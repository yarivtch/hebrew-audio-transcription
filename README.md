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
MIT License - see [LICENSE](LICENSE) for more details.

## 🤝 Contributing
Contributions are welcome! Please read the contributing guidelines before getting started.

## ✨ New Features
- 🔊 Support for various audio formats (MP3, OGG, WAV, etc.)
- 💬 Modern chat-style user interface
- 🚀 Automatic conversion to WAV format on the client-side
- 📱 Responsive design suitable for all devices
- 🎯 Full support for Hebrew and RTL direction
- ⚡ Fast and efficient processing

## 🛠️ Updated Technologies
### Client-side
- Vanilla JavaScript
- HTML5 & CSS3
- Web Audio API for format conversion
- Google Fonts (Rubik)
- Material Icons

### Server-side
- Python Flask
- Faster Whisper for transcription
- NumPy & SciPy for audio processing

## 📋 System Requirements
### Server
- Python 3.8 and above
- pip (Python package manager)
- Minimum 4GB RAM
- Recommended 4 cores and above

### Client
- Modern browser with support for:
  - Web Audio API
  - Modern JavaScript
  - CSS Grid & Flexbox

## 🚀 Installation
1. Clone the repository:
```bash
git clone https://github.com/your-username/hebrew-transcription.git
cd hebrew-transcription
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the server:
```bash
python server/server.py
```

4. Access the application at `http://localhost:5002`

## 💡 Usage
1. Click the "Upload File" button and select an audio file
2. The system will display the selected file name in the chat interface
3. Click the "Transcribe" button to start the process
4. Wait for the transcription to complete
5. The transcription will be displayed in the chat interface

## 📦 Dependencies
```
faster-whisper==0.9.0
Flask==2.3.2
numpy==1.24.3
scipy==1.11.4
```

## 🔒 Security
- Verification of file type on both client and server sides
- Format conversion on the client-side
- Comprehensive error handling
- Detailed logs for monitoring

## 🎨 User Interface
- Modern and clean design
- Rubik font for optimal readability
- Smooth animations
- Clear visual feedback
- Full support for RTL

## 🔜 Planned Improvements
- [ ] Direct microphone input
- [ ] Saving transcription history
- [ ] Exporting to various formats
- [ ] Speaker identification
- [ ] Transcription editing
- [ ] Progressive Web App (PWA)
