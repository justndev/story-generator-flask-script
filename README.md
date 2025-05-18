# 🧠 Story Generator Flask API

A Python Flask-based API that generates short narrated videos with captions, using background videos, OpenAI text-to-speech, and FFmpeg for media processing.
It is a microservice part of Story Generator project. It specifically used for generating videos. Example of generated video can be seen here: https://drive.google.com/file/d/1cQNQwtLhTILZgekAuNhYGvPC-SLked3F/view?usp=sharing

## 🚀 Features

- Convert a given story/script to voice using OpenAI's TTS
- Overlay the voice and captions onto a background video
- Asynchronous job processing with real-time status checking
- Periodic cleanup of temporary media files

## 📁 Project Structure

```
src/
├── bg_videos/
│   ├── links.py                # Dictionary of background video paths
│   ├── mc_parkour_X.mp4        # Background video files (ignored in Git)
│   └── temp_*                  # Temporary folders for media processing
├── app.py                      # Flask app and API endpoints
├── generator.py                # Core video/audio generation logic
.env                            # Environment file for API key
requirements.txt                # Python dependencies
```

## 🔧 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/justndev/story-generator-flask-script-api.git
   cd story-generator-flask-script-api
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install captacity[local_whisper]
   ```

4. **Set up environment variables**

   Create a `.env` file in the root directory:
   ```ini
   OPENAI_API_KEY=your_openai_api_key_here
   ```

5. **Run the Flask API**
   ```bash
   python src/app.py
   ```

## 🧠 How It Works

You send a POST request to `/generate` with:
- `text`: the script/story
- `bgVideoId`: the key of a video from bg_videos/links.py
- `uid`: unique identifier for the session
- `voice`: OpenAI TTS voice name (e.g., "nova", "shimmer")

The server:
1. Converts text to speech using OpenAI API
2. Adds voiceover to background video
3. Adds captions
4. Returns the ready video path when completed

You can check job status via `/status?uid=<your_uid>`.

## 🎯 API Endpoints

### POST /generate
Start a video generation job.

**Request**
```json
{
  "text": "Once upon a time...",
  "bgVideoId": "mc_parkour_1",
  "uid": "unique-session-id",
  "voice": "nova"
}
```

**Response**
```json
{
  "status": "queued",
  "uid": "unique-session-id"
}
```

### GET /status?uid=<uid>
Check job status.

**Response**
```json
{
  "uid": "unique-session-id",
  "status": "completed"  // or "processing", "queued", "failed"
}
```

### GET /health
Health check endpoint to verify if the API is running.

## 📦 Requirements

- Python 3.7+
- FFmpeg installed and accessible in your system path
- OpenAI API key (for TTS)

## ⚙️ Background Cleanup

A background thread periodically deletes old temporary files (>10 mins old) from:
- temp_voices
- temp_voiced_videos
- temp_captured_videos

## 🛡️ Environment Variables

Set in `.env`:
```
OPENAI_API_KEY=your_openai_api_key_here
```

## 📁 .gitignore

```
# Bytecode and cache
__pycache__/
*.pyc

# Virtual environments
venv/

# Environment variables
.env

# Ignore videos and temp outputs
src/bg_videos/*.mp4
src/bg_videos/temp_voices/
src/bg_videos/temp_voiced_videos/
src/bg_videos/temp_captured_videos/
src/bg_videos/temp_ready_videos/
```

## 📞 Support

For issues, please open a GitHub issue or submit a pull request with improvements.

## 📝 License

MIT License.
