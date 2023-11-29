import json
import shutil
import os
import requests

bearer_auth_token = ""
DOLBY_OUTPUT_LOCATION = "dlb://out/example-metadata.json"
APP_KEY = "VcFmdohP1JtHZKIjb0MR1g=="
APP_SECRET = "DQaaIIggfBqh_6B2qMvPOI9sV5cACqEoexoze3-QnRE="
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
    # print(bearer_auth_token)

    return bearer_auth_token


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
        "input": s3_reference,
        "output": DOLBY_OUTPUT_LOCATION
    }

    response = requests.post(analyse_speech_url, json=body, headers=headers)
    response.raise_for_status()
    job_id = response.json()["job_id"]
    print(job_id)

    return job_id


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


def download_results():
    # print("fetching Dolby access token")
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
    # local_output_path = "output.json"
    data = None
    with requests.get(url, params=args, headers=headers, stream=True) as response:
        print(response)
        response.raise_for_status()
        response.raw.decode_content = True
        # Code to get the JSON object stored at "response.url" and return it in JSON form
        data = requests.get(response.url, stream=True)
    return data.json()
