from flask import Flask, request, jsonify
import threading
import time
import os
from pathlib import Path
import logging

from generator import generate_short_video

app = Flask(__name__)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("app")

job_statuses = {}


def cleanup_old_files():
    """Background thread to clean up old files in multiple directories"""
    logger.info("Starting background cleanup thread for multiple directories")

    while True:
        try:
            max_age_minutes = 10
            logger.info(f"Checking for files older than {max_age_minutes} minutes in specified directories")

            current_time = time.time()
            max_age_seconds = max_age_minutes * 60

            count_deleted = 0
            count_total = 0

            directories = ['temp_voices', 'temp_captured_videos', 'temp_voiced_videos']

            for directory in directories:
                directory_path = Path(directory)

                # Check if directory exists, if not, create it
                if not directory_path.exists():
                    logger.warning(f"Directory {directory} does not exist, creating it")
                    directory_path.mkdir(exist_ok=True)

                # Iterate over the files in the current directory
                for file_path in directory_path.glob('*'):
                    if file_path.is_file():
                        count_total += 1
                        file_age = current_time - os.path.getmtime(file_path)
                        file_age_minutes = file_age / 60

                        logger.debug(
                            f"Found file: {file_path.name} in {directory}, age: {file_age_minutes:.2f} minutes")

                        if file_age > max_age_seconds:
                            try:
                                file_path.unlink()  # Delete the file
                                count_deleted += 1
                                logger.info(f"Deleted old file: {file_path.name} in {directory}")
                            except Exception as e:
                                logger.error(f"Failed to delete {file_path} in {directory}: {str(e)}")

            # Logging the results of the cleanup cycle
            logger.info(f"Cleanup cycle completed: {count_deleted}/{count_total} files deleted across all directories")

        except Exception as e:
            logger.error(f"Error in cleanup thread: {str(e)}")

        # Log before sleep
        logger.info(f"Cleanup thread sleeping for 60 seconds before next check")

        # Sleep for 60 seconds before the next cleanup cycle
        time.sleep(60)

def process_video(text, bg_video_id, uid, voice):
    """Background worker for generating the video."""
    try:
        job_statuses[uid] = "processing"
        output_path = generate_short_video(text, bg_video_id, uid, voice)
        job_statuses[uid] = "completed"
    except Exception as e:
        job_statuses[uid] = f"failed: {str(e)}"

@app.route('/status', methods=['GET'])
def status():
    """Check the status of a video generation job."""
    uid = request.args.get("uid", "")

    if not uid:
        return jsonify({"error": "Missing uid"}), 400

    status = job_statuses.get(uid, "not found")

    return jsonify({"uid": uid, "status": status}), 200

@app.route('/generate', methods=['POST'])
def generate():
    """Start video generation and return immediately."""
    try:
        text = request.json.get("text", "")
        bg_video_id = request.json.get("bgVideoId", "")
        uid = request.json.get("uid", "")
        voice = request.json.get("voice", "")


        if not text or not bg_video_id or not uid:
            return jsonify({"error": "Missing fields"}), 400

        # Mark job as started
        job_statuses[uid] = "queued"

        # Start background thread
        threading.Thread(target=process_video, args=(text, bg_video_id, uid, voice), daemon=True).start()

        return jsonify({"status": "queued", "uid": uid}), 202  # 202 Accepted
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Health check endpoint
@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "running"}), 200


if __name__ == '__main__':
    # Start the cleanup thread before running the app
    cleanup_thread = threading.Thread(target=cleanup_old_files, daemon=True)
    cleanup_thread.start()
    logger.info("Cleanup thread started")

    # Run the Flask app
    app.run(host='0.0.0.0', port=5000, debug=True)