import json
import os
import shutil

import requests
from flask import Flask, request

import dolby_integration
import whisper_api_integration

app = Flask(__name__)


@app.route('/analyseSpeech/<s3_reference>', methods=['GET'])
def analyse_speech(s3_reference):
    return dolby_integration.analyse_speech(s3_reference)


@app.route('/getJobStatus/<job_id>', methods=['GET'])
def get_job_status(job_id):
    return dolby_integration.get_job_status(job_id)


@app.route('/downloadResults/', methods=['GET'])
def download_results():
    return dolby_integration.download_results()


@app.route("/transcribeAudio")
def transcribe_audio():
    audio_reference = request.args.get('ref')
    return whisper_api_integration.transcript_audio(audio_reference)


@app.route("/healthCheck")
def health_check():
    return 'Health check success'


if __name__ == '__main__':
    app.run(port=8080, debug=True)
