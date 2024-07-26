#!/Users/zoppke/venvs/default/bin/python3
# coding: utf-8

# Create 30-minute slices of large M4A files
# ffmpeg -i recording.m4a -f segment -segment_time 1800 -c copy output_audio_%03d.m4a

import openai
import os
import argparse

# gets OPENAI_API_KEY from your environment variables
openai = openai.OpenAI()

file_path = "output_audio_000.m4a"

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

            print(transcript.text)

    except Exception as e:
        print(f"An error occurred: {e}")

"""
Usage:
./whisper.py recording.m4a > transcript.txt
"""

if __name__ == "__main__":

    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Transcribe a voice recording using OpenAI's API.")
    parser.add_argument("file_path", help="Path to the voice file")

    args = parser.parse_args()
    
    # Transcribe the audio file
    transcription = transcribe_audio(args.file_path)

    # print transcript
    if transcription:
        print(transcription)