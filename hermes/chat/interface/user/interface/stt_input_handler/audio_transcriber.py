from groq import Groq


class AudioTranscriber:
    def __init__(self, api_key: str):
        self.client = Groq(api_key=api_key)

    def transcribe(self, audio_file: str) -> str:
        with open(audio_file, "rb") as audio:
            transcript = self.client.audio.transcriptions.create(
                file=(audio_file, audio),
                model="whisper-large-v3-turbo",
                prompt=self._get_transcription_prompt(),
                temperature=0,
                response_format="text",
            )
        return transcript.text

    def _get_transcription_prompt(self) -> str:
        return ("This is a recording of a human message in a chat, please transcribe it as accurately as possible, capture "
                "if the user has a question")
