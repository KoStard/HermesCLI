import os
import select
import sys
import uuid

import numpy as np
import sounddevice as sd
import soundfile as sf

from hermes.utils.overriding_printer import OverridingPrinter


class AudioRecorder:
    def __init__(self, samplerate: int = 44100):
        self.samplerate = samplerate

    def record(self) -> str:
        audio_data = []
        recording = True

        def callback(indata, frames, time, status):
            if status:
                print(status)
            if recording:
                audio_data.append(indata.copy())

        self._flush_input_buffer()
        overriding_printer = self._create_printer()

        overriding_printer.print_next()
        input()

        stream = sd.InputStream(callback=callback, channels=1, samplerate=self.samplerate)
        overriding_printer.print_next(go_to_last_line=True)

        with stream:
            input()
            recording = False

        overriding_printer.print_next(go_to_last_line=True)
        return self._save_audio(audio_data)

    def _flush_input_buffer(self):
        while select.select([sys.stdin], [], [], 0.0)[0]:
            sys.stdin.readline()

    def _create_printer(self) -> OverridingPrinter:
        return OverridingPrinter(
            [
                "Press Enter to start recording! Ctrl+C to fall back to the keyboard.",
                "🔴 Recording... Press Enter to stop.",
                "✅ Recording finished.",
            ]
        )

    def _save_audio(self, audio_data: list) -> str:
        audio_array = np.concatenate(audio_data, axis=0)
        temp_folder = "/tmp/hermes/audio/"

        if not os.path.exists(temp_folder):
            os.makedirs(temp_folder)

        temp_wav = os.path.join(temp_folder, f"temp_recording_{uuid.uuid4()}.wav")
        sf.write(temp_wav, audio_array, self.samplerate)
        return temp_wav
