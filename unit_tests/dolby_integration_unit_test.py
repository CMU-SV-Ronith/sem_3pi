import unittest
from io import BytesIO
from unittest.mock import Mock, patch, mock_open
from dolby_integration import (
    fetch_access_token,
    analyse_speech,
    download_results,
)


class TestDolbyIntegration(unittest.TestCase):

    @patch('requests.post')
    def test_fetch_access_token_success(self, mock_requests_post):
        # Mock the response from the requests.post method
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b'{"access_token": "mock_access_token"}'
        mock_requests_post.return_value = mock_response

        # Set global constants within the scope of this test
        with patch('dolby_integration.bearer_auth_token', ''):
            access_token = fetch_access_token()

        mock_requests_post.assert_called_once_with(
            'https://api.dolby.io/v1/auth/token',
            data={'grant_type': 'client_credentials', 'expires_in': 1800},
            auth=('DJ6SMpz66xDdcFhJCD3kbw==', '-SvLt35dRZSG_CBtObReSenvbHgaIJgQZGaHtPBbtwY=')
        )

        self.assertEqual(access_token, 'mock_access_token')

    @patch('requests.post')
    @patch('requests.get')
    def test_analyse_speech_success(self, mock_requests_get, mock_requests_post):
        # Mock the response from the requests.post method
        mock_response_post = Mock()
        mock_response_post.status_code = 200
        mock_response_post.json.return_value = {"job_id": "mock_job_id"}
        mock_requests_post.return_value = mock_response_post

        # Mock the response from the requests.get method
        mock_response_get = Mock()
        mock_response_get.status_code = 200
        mock_response_get.json.return_value = {"status": "completed"}
        mock_requests_get.return_value = mock_response_get

        s3_reference = "https://dolbyio.s3-us-west-1.amazonaws.com/public/shelby/indoors.original.mp4"

        # Set global constants within the scope of this test
        with patch('dolby_integration.bearer_auth_token', 'mock_access_token'):
            job_id = analyse_speech(s3_reference)

        mock_requests_post.assert_called_once_with(
            'https://api.dolby.com/media/analyze/speech',
            json={
                "input": s3_reference,
                "output": "dlb://out/example-metadata.json"
            },
            headers={
                "Authorization": "Bearer mock_access_token",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        )

        self.assertEqual(job_id, "mock_job_id")

    @patch('requests.get')
    @patch('shutil.copyfileobj')
    @unittest.skip("wip")
    def test_download_results_success(self, mock_shutil_copyfileobj, mock_requests_get):
        # Create a mock response from requests.get
        mock_response = Mock()
        mock_response.status_code = 200

        # Simulate streaming response data
        mock_data = b'mock_data_chunk1' + b'mock_data_chunk2'
        mock_stream = BytesIO(mock_data)

        # Attach the mock stream to the response
        mock_response.iter_content.side_effect = lambda chunk_size: mock_stream.read(chunk_size)

        mock_requests_get.return_value = mock_response

        # Mock the 'open' function
        with patch('builtins.open', mock_open(), create=True) as mock_file:
            local_output_path = "/Users/ronithreddy/Desktop/output.json"
            result = download_results()

        mock_shutil_copyfileobj.assert_called_once()
        mock_file.assert_called_once_with(local_output_path, 'wb')

        self.assertEqual(result, "success!")


if __name__ == '__main__':
    unittest.main()
