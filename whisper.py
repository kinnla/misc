#!/Users/zoppke/venvs/default/bin/python3
# coding: utf-8

# Create 30-minute slices of large M4A files
# ffmpeg -i recording.m4a -f segment -segment_time 1800 -c copy output_audio_%03d.m4a

import openai
import os
import argparse
import subprocess

# Maximum content size limit in bytes (25 MB)
MAX_CONTENT_SIZE = 26214400

# gets OPENAI_API_KEY from your environment variables
openai = openai.OpenAI()

def get_audio_bitrate(file_path):
    # Use ffprobe to get the bitrate of the audio file in bps
    result = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0", 
                             "-show_entries", "stream=bit_rate", 
                             "-of", "default=noprint_wrappers=1:nokey=1", file_path],
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return int(result.stdout)

def transcode_to_64kbps(file_path, temp_dir):
    # Generate a new file path for the transcoded file in the temp directory
    base_name = os.path.basename(file_path)
    new_file_path = os.path.join(temp_dir, base_name)
    
    # Transcode the file to 64 kbps using ffmpeg
    command = ["ffmpeg", "-i", file_path, "-b:a", "64k", new_file_path]
    subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    return new_file_path

def get_audio_duration(file_path):
    # Use ffprobe to get the duration of the audio file in seconds
    result = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                             "-of", "default=noprint_wrappers=1:nokey=1", file_path],
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return float(result.stdout)

def split_audio(file_path, temp_dir):
    # Split the audio file into 30-minute segments
    segment_files = []
    command = ["ffmpeg", "-i", file_path, "-f", "segment", "-segment_time", "1800", "-c", 
                "copy", os.path.join(temp_dir, "output_audio_%03d.m4a")]    
    subprocess.run(command)
    for file in sorted(os.listdir(temp_dir)):
        if file.startswith("output_audio_") and file.endswith(".m4a"):
            segment_files.append(os.path.join(temp_dir, file))
    return segment_files

def transcribe_audio(file_path):
    
    # Ensure the file exists
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file {file_path} does not exist")

    try:
        # Open the file in binary mode
        with open(file_path, 'rb') as audio_file:
            
            # Send the file to OpenAI for transcription
            transcript = openai.audio.transcriptions.create(
                model="whisper-1",  # Specify the Whisper model
                file=audio_file
            )
            return transcript.text

    except Exception as e:
        print(f"An error occurred: {e}")
        return None

"""
Usage:
./whisper.py recording.m4a
"""

if __name__ == "__main__":

    # Set up argument parsing
    parser = argparse.ArgumentParser(description=
        "Transcribe a voice recording using OpenAI's API.")
    parser.add_argument("file_path", help="Path to the voice file")

    args = parser.parse_args()
    temp_dir = "temp_audio"
    os.makedirs(temp_dir, exist_ok=True)
    
    # Check the file size
    file_size = os.path.getsize(args.file_path)
    if file_size > MAX_CONTENT_SIZE:
        # Check the bitrate
        bitrate = get_audio_bitrate(args.file_path)
        if bitrate > 64000:
            print(f"Bitrate ({bitrate} bps) is greater than 64 kbps. Transcoding the file...")
            args.file_path = transcode_to_64kbps(args.file_path, temp_dir)

    # Check the duration of the audio file
    duration = get_audio_duration(args.file_path)

    # If the audio is longer than 30 minutes, split it
    if duration > 1800:
        print("Splitting audio into 30-minute segments...")
        segment_files = split_audio(args.file_path)
    else:
        segment_files = [args.file_path]

    # Transcribe each segment and write to text file
    transcript_path = os.path.join(temp_dir, "transcript.txt")
    with open(transcript_path, 'w') as transcript_file:
        for segment in segment_files:
            print(f"Transcribing {segment}...")
            transcription = transcribe_audio(segment)
            if transcription:
                transcript_file.write(transcription + "\n")
                print(f"Segment {segment} transcribed successfully.")