import unittest
from main import app
from unittest.mock import patch


class TestAppRoutes(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()

    def test_analyse_speech_route(self):
        with patch('dolby_integration.analyse_speech', return_value='mock_job_id'):
            response = self.app.get('/analyseSpeech/mock_s3_reference')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.get_data(as_text=True), 'mock_job_id')

    def test_get_job_status_route(self):
        with patch('dolby_integration.get_job_status', return_value='mock_status'):
            response = self.app.get('/getJobStatus/mock_job_id')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.get_data(as_text=True), 'mock_status')

    def test_download_results_route(self):
        with patch('dolby_integration.download_results', return_value='mock_success'):
            response = self.app.get('/downloadResults/')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.get_data(as_text=True), 'mock_success')

    @patch('whisper_api_integration.transcript_audio', return_value='mock_transcription')
    def test_transcribe_audio_route(self, mock_transcribe_audio):
        response = self.app.get('/transcribeAudio?ref=mock_audio_reference')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_data(as_text=True), 'mock_transcription')
        mock_transcribe_audio.assert_called_once_with('mock_audio_reference')

    def test_health_check_route(self):
        response = self.app.get('/healthCheck')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_data(as_text=True), 'Health check success')


if __name__ == '__main__':
    unittest.main()
