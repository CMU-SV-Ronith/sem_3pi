import unittest
from unittest.mock import patch, MagicMock
from openai_text_analyzer import openai_complete


class TestOpenAIComplete(unittest.TestCase):

    @patch('openai_text_analyzer.ChatOpenAI')
    @patch('openai_text_analyzer.LLMChain')
    def test_openai_complete_success(self, mock_llm_chain, mock_chat):
        mock_llm_chain.return_value.run.return_value = "Expected Result"

        result = openai_complete("test prompt")

        self.assertEqual(result, "Expected Result")

    @patch('openai_text_analyzer.ChatOpenAI')
    @patch('openai_text_analyzer.LLMChain')
    def test_openai_complete_empty_prompt(self, mock_llm_chain, mock_chat):
        expected_mock_return = MagicMock()
        mock_llm_chain.return_value.run.return_value = expected_mock_return

        result = openai_complete("")

        self.assertEqual(result, expected_mock_return)


if __name__ == '__main__':
    unittest.main()
