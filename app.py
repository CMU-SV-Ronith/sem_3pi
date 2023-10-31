import json
import os
import shutil

import requests
from flask import Flask

app = Flask(__name__)

bearer_auth_token = ""
DOLBY_OUTPUT_LOCATION = "dlb://out/example-metadata.json"
APP_KEY = "DJ6SMpz66xDdcFhJCD3kbw=="
APP_SECRET = "-SvLt35dRZSG_CBtObReSenvbHgaIJgQZGaHtPBbtwY="
analyse_speech_url = "https://api.dolby.com/media/analyze/speech"


def fetch_access_token():
    global bearer_auth_token

    if bearer_auth_token != "":
        return bearer_auth_token

    payload = {
        'grant_type': 'client_credentials',
        'expires_in': 1800
    }
    response = requests.post(
        'https://api.dolby.io/v1/auth/token',
        data=payload,
        auth=(APP_KEY, APP_SECRET)
    )
    body = json.loads(response.content)
    bearer_auth_token = body['access_token']
    print(bearer_auth_token)

    return bearer_auth_token


@app.route('/analyseSpeech/<s3_reference>', methods=['GET'])
def analyse_speech(s3_reference):
    global bearer_auth_token

    print(f"Received speech analysis for {s3_reference}")

    print("fetching Dolby access token")
    try:
        bearer_auth_token = fetch_access_token()
    except Exception:
        print("error in fetching bearer token")

    headers = {
        "Authorization": "Bearer {0}".format(bearer_auth_token),
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    body = {
        "input": "https://dolbyio.s3-us-west-1.amazonaws.com/public/shelby/indoors.original.mp4",
        "output": DOLBY_OUTPUT_LOCATION
    }

    response = requests.post(analyse_speech_url, json=body, headers=headers)
    response.raise_for_status()
    job_id = response.json()["job_id"]
    print(job_id)

    return job_id


@app.route('/getJobStatus/<job_id>', methods=['GET'])
def get_job_status(job_id):
    global bearer_auth_token

    print(f"getting job statues for {job_id}")

    print("fetching Dolby access token")
    try:
        bearer_auth_token = fetch_access_token()
    except Exception:
        print("error in fetching bearer token")

    headers = {
        "Authorization": "Bearer {0}".format(bearer_auth_token),
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    params = {
        "job_id": job_id,
    }

    response = requests.get(analyse_speech_url, params=params, headers=headers)
    response.raise_for_status()
    print(response.json())

    return response.json()


@app.route('/downloadResults/', methods=['GET'])
def download_results():

    print("fetching Dolby access token")
    try:
        bearer_auth_token = fetch_access_token()
    except Exception:
        print("error in fetching bearer token")

    url = "https://api.dolby.com/media/output"
    headers = {
        "Authorization": "Bearer {0}".format(bearer_auth_token),
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    args = {
        "url": DOLBY_OUTPUT_LOCATION,
    }
    local_output_path = "/Users/ronithreddy/Desktop/output.json"
    with requests.get(url, params=args, headers=headers, stream=True) as response:
        response.raise_for_status()
        response.raw.decode_content = True
        print("Downloading from {0} into {1}".format(response.url, local_output_path))
        with open(local_output_path, "wb") as output_file:
            shutil.copyfileobj(response.raw, output_file)

    return "success!"


if __name__ == '__main__':
    app.run(port=8080)
