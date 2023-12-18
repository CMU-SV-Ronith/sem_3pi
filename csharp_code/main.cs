using System; // Add this line
using UnityEngine;
using System.IO;
using Amazon.S3; // Ensure AWS SDK is imported
using Amazon.S3.Model;
using UnityEngine.UI;
using Amazon.Runtime;
using UnityEngine.Networking;
using System.Collections;
using System.Threading.Tasks;
using System.Linq;
using UnityEngine.Events;
using System.Collections;
using System.Collections.Generic;
[System.Serializable]
public class RequestData
{
    public string prompt;
}

[Serializable]
public class AnalysisResponse
{
    // Define the structure according to the JSON response
    public ProcessedRegion processed_region;
    // Other fields as necessary

    [Serializable]
    public class ProcessedRegion
    {
        public AudioData audio;
        // Other fields as necessary
    }

    [Serializable]
    public class AudioData
    {
        public SpeechData speech;
        // Other fields as necessary
    }

    [Serializable]
    public class SpeechData
    {
        public Detail[] details;
        // Other fields as necessary
    }

    [Serializable]
    public class Detail
    {
        public float longest_monologue;
        public LoudnessData loudness;
        public Section[] sections;
        public float quality_score;
        // Other fields as necessary
    }

    [Serializable]
    public class LoudnessData
    {
        public float measured;
        // Other fields as necessary
    }

    [Serializable]
    public class Section
    {
        public float confidence;
        // Other fields as necessary
    }
}

namespace OpenAI
{
    public class Whisper : MonoBehaviour
    {
        [SerializeField] private Button recordButton;
        [SerializeField] private Image progressBar;
        [SerializeField] private Text message;
        [SerializeField] private Dropdown dropdown;

        private readonly string fileName = "output.wav";
        private readonly int duration = 30;

        private AudioClip clip;
        private bool isRecording;
        private float time;
        private OpenAIApi openai = new OpenAIApi("wiefwx");

        public string baseUrl = "https://416c-209-129-244-192.ngrok.io";
        public GameObject button;
        public UnityEvent onPress;
        public UnityEvent onRelease;
        GameObject presser;
        bool isPressed;

        private void Start()
        {
            isPressed = false;
#if UNITY_WEBGL && !UNITY_EDITOR
            dropdown.options.Add(new Dropdown.OptionData("Microphone not supported on WebGL"));
#else
            foreach (var device in Microphone.devices)
            {
                dropdown.options.Add(new Dropdown.OptionData(device));
            }
            recordButton.onClick.AddListener(StartRecording);
            dropdown.onValueChanged.AddListener(ChangeMicrophone);

            // TriggerRecordButton();

            var index = PlayerPrefs.GetInt("user-mic-device-index");
            dropdown.SetValueWithoutNotify(index);
#endif
        }
        public void TriggerRecordButton()
        {
            if (recordButton != null)
            {
                recordButton.onClick.Invoke();
            }
        }
        private void OnTriggerEnter(Collider other)
        {
            if (!isPressed)
            {
                button.transform.localPosition = new Vector3(button.transform.localPosition.x, button.transform.localPosition.y - 0.1f, button.transform.localPosition.z);
                presser = other.gameObject;
                onPress.Invoke();
            }
        }

        private void OnTriggerExit(Collider other)
        {
            if (isPressed)
            {
                button.transform.localPosition = new Vector3(button.transform.localPosition.x, button.transform.localPosition.y + 0.1f, button.transform.localPosition.z);
                // presser = null;
                onRelease.Invoke();
                isPressed = false;
            }
        }



        private void ChangeMicrophone(int index)
        {
            PlayerPrefs.SetInt("user-mic-device-index", index);
        }

        private void StartRecording()
        {
            isRecording = true;
            recordButton.enabled = false;

            var index = PlayerPrefs.GetInt("user-mic-device-index");

#if !UNITY_WEBGL
            clip = Microphone.Start(dropdown.options[index].text, false, duration, 44100);
#endif
        }

        private async void EndRecording()
        {
            message.text = "Transcripting...";

#if !UNITY_WEBGL
            Microphone.End(null);
#endif

            byte[] data = SaveWav.Save(fileName, clip);

            // Save locally
            string localPath = Path.Combine(Application.persistentDataPath, fileName);
            File.WriteAllBytes(localPath, data);
            Debug.Log("Saved recording locally at: " + localPath);

            StartCoroutine(UploadAndAnalyze(localPath));
        }


        private void Update()
        {
            if (isRecording)
            {
                time += Time.deltaTime;
                progressBar.fillAmount = time / duration;

                if (time >= duration)
                {
                    time = 0;
                    isRecording = false;
                    EndRecording();
                }
            }
        }
        private IEnumerator UploadAndAnalyze(string localPath)
        {
            Debug.Log(baseUrl);
            // Get transcription and analyze text
            var req = new CreateAudioTranscriptionsRequest
            {
                FileData = new FileData() { Data = File.ReadAllBytes(localPath), Name = "audio.wav" },
                Model = "whisper-1",
                Language = "en"
            };

            var transcriptionTask = openai.CreateAudioTranscription(req);
            yield return new WaitUntil(() => transcriptionTask.IsCompleted);

            if (transcriptionTask.Exception != null)
            {
                Debug.LogError("Transcription failed: " + transcriptionTask.Exception);
                yield break;
            }

            var res = transcriptionTask.Result;
            Debug.Log(res);
            // Set the text to res.Text for the time being
            message.text = res.Text;
            StartCoroutine(AnalyzeText(res.Text));

            // Upload file and wait for the result
            Task<string> uploadTask = UploadFileToS3(localPath, "recontact-temp-recording-bucket");
            yield return new WaitUntil(() => uploadTask.IsCompleted);

            if (uploadTask.Exception != null)
            {
                Debug.LogError("Upload failed: " + uploadTask.Exception);
                yield break;
            }

            string fileUrl = uploadTask.Result;
            Debug.Log("File uploaded successfully. URL: " + fileUrl);
            StartCoroutine(AnalyseSpeech(fileUrl));

            // Wait before getting results
            yield return new WaitForSeconds(15);

            // Get analysis results
            StartCoroutine(GetAnalysisResults());
        }

        [System.Serializable]
        public class RequestData
        {
            public string prompt;
        }

        private IEnumerator AnalyzeText(string transcript)
        {
            RequestData requestData = new RequestData { prompt = transcript };
            string json = JsonUtility.ToJson(requestData);
            Debug.Log("JSON being sent: " + json);

            byte[] jsonToSend = new System.Text.UTF8Encoding().GetBytes(json);
            var request = new UnityWebRequest(baseUrl + "/analyzeText", "POST")
            {
                uploadHandler = new UploadHandlerRaw(jsonToSend),
                downloadHandler = new DownloadHandlerBuffer()
            };
            request.SetRequestHeader("Content-Type", "application/json");

            yield return request.SendWebRequest();

            if (request.isNetworkError || request.isHttpError)
            {
                Debug.LogError("Error: " + request.error);
                Debug.LogError("Response: " + request.downloadHandler.text);
            }
            else
            {
                string responseText = request.downloadHandler.text;
                Debug.Log("Response: " + responseText);
                string temp = message.text;
                message.text = responseText + "\n" + temp;
            }
        }

        private IEnumerator GetAnalysisResults()
        {
            var request = UnityWebRequest.Get(baseUrl + "/getResults");

            yield return request.SendWebRequest();

            if (request.isNetworkError || request.isHttpError)
            {
                Debug.LogError("Error: " + request.error);
            }
            else
            {
                var responseJson = JsonUtility.FromJson<AnalysisResponse>(request.downloadHandler.text);
                var analysisObject = new
                {
                    Loudness = responseJson.processed_region.audio.speech.details[0].loudness.measured,
                    Confidence = responseJson.processed_region.audio.speech.details[0].sections[0].confidence,
                    Quality = responseJson.processed_region.audio.speech.details[0].quality_score,
                    LongestMonologue = responseJson.processed_region.audio.speech.details[0].longest_monologue
                };
                // Display analysisObject values in the UI
                Debug.Log(analysisObject);
                // Map over the analysisObject and convert it into a string with comma separated key-value pairs
                var analysisString = string.Join(", ", analysisObject.GetType().GetProperties().Select(x => $"{x.Name}: {x.GetValue(analysisObject)}"));


                var tempVal = message.text;
                message.text = tempVal + "\n" + analysisString;
            }
        }

        [System.Serializable]
        public class RequestData2
        {
            public string input;
        }
        private IEnumerator AnalyseSpeech(string fileUrl)
        {
            Debug.Log("Analyzing speech... for this file" + fileUrl);
            RequestData2 requestData = new RequestData2 { input = fileUrl };
            string json = JsonUtility.ToJson(requestData);
            Debug.Log("JSON being sent: " + json);

            byte[] jsonToSend = new System.Text.UTF8Encoding().GetBytes(json);
            var request = new UnityWebRequest(baseUrl + "/analyseSpeech", "POST")
            {
                uploadHandler = new UploadHandlerRaw(jsonToSend),
                downloadHandler = new DownloadHandlerBuffer()
            };
            request.SetRequestHeader("Content-Type", "application/json");
            // request.SetRequestHeader("x-api-key", "YOUR_API_KEY"); // Replace with your actual API key

            yield return request.SendWebRequest();

            if (request.isNetworkError || request.isHttpError)
            {
                Debug.LogError("Error: " + request.error);
            }
            else
            {
                string audioString = request.downloadHandler.text;
                string temp = message.text;
                message.text = audioString + "\n" + temp;
            }
        }

        private async Task<string> UploadFileToS3(string filePath, string bucketName)
        {
            // Hardcoded credentials (not recommended for production)
            string awsAccessKeyId = "AKIAX";
            string awsSecretAccessKey = "fY";
            AWSCredentials credentials = new BasicAWSCredentials(awsAccessKeyId, awsSecretAccessKey);
            AmazonS3Client s3Client = new AmazonS3Client(credentials, Amazon.RegionEndpoint.USEast1); // Initialize with your AWS credentials

            try
            {
                // Create a PutObject request
                PutObjectRequest putRequest = new PutObjectRequest
                {
                    BucketName = bucketName,
                    FilePath = filePath,
                    Key = Path.GetFileName(filePath),
                    CannedACL = S3CannedACL.PublicRead // Set the file to be publicly accessible
                };

                PutObjectResponse response = await s3Client.PutObjectAsync(putRequest);

                if (response.HttpStatusCode == System.Net.HttpStatusCode.OK)
                {
                    string fileUrl = $"https://{bucketName}.s3.amazonaws.com/{Path.GetFileName(filePath)}";
                    Debug.Log("File uploaded successfully. URL: " + fileUrl);
                    return fileUrl; // Return the URL
                }
                else
                {
                    Debug.LogError("Failed to upload file. HTTP Status Code: " + response.HttpStatusCode);
                    return null; // Return null if upload failed
                }
            }
            catch (AmazonS3Exception e)
            {
                Debug.LogError("Error encountered on server. Message:'" + e.Message + "'");
                return null; // Return null on exception
            }
            catch (Exception e)
            {
                Debug.LogError("Unknown encountered on server. Message:'" + e.Message + "'");
                return null; // Return null on exception
            }
        }

    }
}