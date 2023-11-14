import unittest
from unittest.mock import patch, mock_open
from whisper_api_integration import transcript_audio


class TestTranscriptAudio(unittest.TestCase):

    @patch('openai.Audio.transcribe')
    def test_transcript_audio_success(self, mock_transcribe):
        # Mock the response from the OpenAI API
        mock_transcribe.return_value = {'text': 'This is a test transcription.'}

        # Mock the open function to return a file-like object
        with patch('builtins.open', mock_open(read_data=b'sample_audio_data')) as mock_file:
            audio_reference = 'sample_audio.wav'  # Replace with your sample audio file path

            transcribed_text = transcript_audio(audio_reference)

            # Ensure that the open method is called with the correct file path
            mock_file.assert_called_once_with(audio_reference, 'rb')

        # Ensure that the OpenAI API call is made with the correct arguments
        mock_transcribe.assert_called_once_with("whisper-1", mock_file.return_value)

        # Verify the result
        self.assertEqual(transcribed_text, 'This is a test transcription.')


if __name__ == '__main__':
    unittest.main()
