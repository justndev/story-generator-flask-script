import os
import subprocess
import sys
import json
import captacity

from pathlib import Path
from openai import OpenAI, OpenAIError
from dotenv import load_dotenv

load_dotenv()
# Access the variable
api_key = os.getenv("OPENAI_API_KEY")

from bg_videos.links import links

def create_voice(text: str, uid: str, voice: str):
    client = OpenAI(api_key=api_key)
    try:
        speech_file_path = Path(__file__).parent / f"temp_voices/{uid}.mp3"
        response = client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text
        )

        response.stream_to_file(speech_file_path)

        return {
            "success": True,
            "path": speech_file_path,
        }

    except ValueError as ve:
        print(f"Value Error: {ve}")
        return {"success": False, "error": str(ve)}

    except OpenAIError as oe:
        print(f"OpenAI API Error: {oe}")
        return {"success": False, "error": str(oe)}

    except Exception as e:
        print(f"Unexpected Error: {e}")
        return {"success": False, "error": str(e)}

def delete_temp_files_by_id(uid):
    temp_voice_path = f"temp_voices/{uid}.mp3"
    temp_voiced_video_path = f"temp_voiced_videos/{uid}.mp4"
    temp_captured_video_path = f"temp_captured_videos/{uid}.mp4"

    paths = [temp_voiced_video_path, temp_voice_path, temp_captured_video_path]
    for path in paths:
        try:
            os.remove(path)
            print("File deleted successfully.")
        except FileNotFoundError:
            print("The file does not exist.")
        except PermissionError:
            print("You do not have permission to delete the file.")
        except Exception as e:
            print(f"An error occurred: {e}")

def delete_temp_ready_video_by_id(uid):
    temp_ready_video_path = f"temp_ready_videos/{uid}.mp4"

    try:
        os.remove(temp_ready_video_path)
        print("File deleted successfully.")
    except FileNotFoundError:
        print("The file does not exist.")
    except PermissionError:
        print("You do not have permission to delete the file.")
    except Exception as e:
        print(f"An error occurred: {e}")

def get_media_duration(file_path):
    cmd = [
        'ffprobe',
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'json',
        file_path
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        data = json.loads(result.stdout)
        return float(data['format']['duration'])
    except Exception as e:
        print(f"Error getting duration for {file_path}: {str(e)}")
        return 0

def add_audio_to_video(video_path, audio_path, output_path, max_audio_duration=120):
    try:
        print(video_path)
        print(audio_path)
        print(output_path)
        audio_duration = get_media_duration(audio_path)
        video_duration = get_media_duration(video_path)

        print(f"Original audio duration: {audio_duration:.2f} seconds")
        print(f"Original video duration: {video_duration:.2f} seconds")

        final_audio_duration = min(audio_duration, max_audio_duration)
        audio_needs_trimming = audio_duration > max_audio_duration

        temp_audio_path = audio_path
        if audio_needs_trimming:
            temp_audio_path = "temp_trimmed_audio.mp3"
            trim_cmd = [
                'ffmpeg',
                '-i', audio_path,
                '-t', str(max_audio_duration),
                '-c:a', 'copy',
                temp_audio_path,
                '-y'
            ]
            subprocess.run(trim_cmd, capture_output=True)
            print(f"Trimmed audio to {max_audio_duration} seconds")

        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-i', temp_audio_path,
            '-map', '0:v',  # Use video from first input
            '-map', '1:a',  # Use audio from second input
            '-c:v', 'copy',  # Copy video codec (no re-encoding)
        ]

        if final_audio_duration < video_duration:
            cmd.extend(['-t', str(final_audio_duration)])
            print(f"Trimming video to match audio duration: {final_audio_duration:.2f} seconds")

        cmd.extend([output_path, '-y'])

        process = subprocess.run(cmd, capture_output=True, text=True)

        if process.returncode == 0:
            print(f"Successfully created video with new audio: {output_path}")
        else:
            print(f"An error occurred with FFmpeg:")
            if process.stderr:
                print(process.stderr)

        if audio_needs_trimming and os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)

    except Exception as e:
        print(f"An error occurred: {str(e)}")

def generate_short_video(text: str, video_id, uid, voice: str):
    try:

        result = create_voice(text, uid, voice)

        if result["success"]:
            output = f"temp_voiced_videos/{uid}.mp4"
            add_audio_to_video(links[video_id], f"temp_voices/{uid}.mp3", output)
            captacity.add_captions(output, f"temp_captured_videos/{uid}.mp4", print_info=True)
            add_audio_to_video(f"temp_captured_videos/{uid}.mp4", f"temp_voices/{uid}.mp3",
                               f"temp_ready_videos/{uid}.mp4")
            delete_temp_files_by_id(uid)
            return f"temp_ready_videos/{uid}.mp4"
    except Exception as e:
        print(f"Error: {e}")

