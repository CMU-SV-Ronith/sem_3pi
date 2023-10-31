import os

import openai


def transcript_audio(audio_reference):
    file = open(audio_reference, "rb")
    openai.api_key = "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"
    return openai.Audio.transcribe("whisper-1", file)['text']
