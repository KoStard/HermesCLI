import os
import sys

from hermes.chat.interface.user.interface.stt_input_handler.audio_recorder import AudioRecorder
from hermes.chat.interface.user.interface.stt_input_handler.audio_transcriber import AudioTranscriber
from hermes.chat.interface.user.interface.stt_input_handler.file_cleaner import FileCleaner


class STTInputHandler:
    def __init__(self, api_key: str):
        self.audio_recorder = AudioRecorder()
        self.audio_transcriber = AudioTranscriber(api_key)
        self.file_cleaner = FileCleaner()

    def get_input(self) -> str:
        audio_file = self.audio_recorder.record()
        text = self.audio_transcriber.transcribe(audio_file)
        self.file_cleaner.cleanup(audio_file)
        return text


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
