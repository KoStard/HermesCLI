import os
import select
import sys

from hermes.utils.overriding_printer import OverridingPrinter


class STTInputHandler:
    def __init__(self, api_key: str):
        self.api_key = api_key

    def get_input(self) -> str:
        audio_file = self.record_audio()
        text = self.transcribe_audio(audio_file)
        self.cleanup(audio_file)
        return text

    def record_audio(self) -> str:
        import uuid

        import numpy as np
        import sounddevice as sd
        import soundfile as sf

        samplerate = 44100
        # Initialize recording flag
        recording = True

        # Create array to store audio data
        audio_data = []

        # Define callback function for the stream
        def callback(indata, frames, time, status):
            if status:
                print(status)
            if recording:
                audio_data.append(indata.copy())

        # Flush input buffer to discard any pending Enter key presses
        while select.select([sys.stdin], [], [], 0.0)[0]:
            sys.stdin.readline()

        overriding_printer = OverridingPrinter(
            [
                "Press Enter to start recording! Ctrl+C to fall back to the keyboard.",
                "🔴 Recording... Press Enter to stop.",
                "✅ Recording finished.",
            ]
        )

        overriding_printer.print_next()
        input()

        # Create input stream
        stream = sd.InputStream(callback=callback, channels=1, samplerate=samplerate)

        # Show recording status
        overriding_printer.print_next(go_to_last_line=True)

        # Start recording
        with stream:
            # Wait for Enter key
            input()
            recording = False
        # Clear previous line and show completion message
        overriding_printer.print_next(go_to_last_line=True)

        # Convert recorded data to numpy array
        audio_array = np.concatenate(audio_data, axis=0)

        # Save as WAV first (temporary file)
        temp_folder = "/tmp/hermes/audio/"
        # Make the folder
        if not os.path.exists(temp_folder):
            os.makedirs(temp_folder)

        # Use a unique name for the file
        temp_wav = os.path.join(temp_folder, f"temp_recording_{uuid.uuid4()}.wav")
        sf.write(temp_wav, audio_array, samplerate)
        return temp_wav

    def transcribe_audio(self, audio_file: str) -> str:
        from groq import Groq

        client = Groq(api_key=self.api_key)

        with open(audio_file, "rb") as audio:
            transcript = client.audio.transcriptions.create(
                file=(audio_file, audio),
                model="whisper-large-v3-turbo",
                prompt="This is a recording of a human message in a chat, please transcribe it as accurately as possible, capture "
                "if the user has a question",
                temperature=0,
                response_format="text",
            )
        return transcript.text

    def cleanup(self, audio_file: str):
        os.remove(audio_file)


if __name__ == "__main__":
    import configparser

    config = configparser.ConfigParser()
    config.read(os.path.expanduser("~/.config/hermes/config.ini"))
    try:
        api_key = config["GROQ"]["api_key"]
    except KeyError:
        print("Please set the GROQ api key in ~/.config/hermes/config.ini")
        sys.exit(1)
    stt_input_handler = STTInputHandler(api_key=config["GROQ"]["api_key"])

    while True:
        print(stt_input_handler.get_input())
