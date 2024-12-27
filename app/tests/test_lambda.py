import unittest
from unittest.mock import patch, MagicMock
from app.lambda import handler, download_file_from_url, download_video_from_s3

class TestLambdaFunction(unittest.TestCase):

    @patch('app.lambda.requests.get')
    def test_download_file_from_url_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'Test content'
        mock_get.return_value = mock_response

        result = download_file_from_url("https://example.com/file.txt", "/tmp/file.txt")
        self.assertTrue(result)

    @patch('app.lambda.requests.get')
    def test_download_file_from_url_failure(self, mock_get):
        mock_get.side_effect = requests.exceptions.RequestException("Error")

        result = download_file_from_url("https://example.com/file.txt", "/tmp/file.txt")
        self.assertFalse(result)

    @patch('app.lambda.s3_client.download_fileobj')
    def test_download_video_from_s3_success(self, mock_download_fileobj):
        mock_download_fileobj.return_value = None

        result = download_video_from_s3("test-bucket", "test-key", "/tmp/video.mp4")
        self.assertTrue(result)

    @patch('app.lambda.s3_client.download_fileobj')
    def test_download_video_from_s3_failure(self, mock_download_fileobj):
        mock_download_fileobj.side_effect = Exception("Error")

        result = download_video_from_s3("test-bucket", "test-key", "/tmp/video.mp4")
        self.assertFalse(result)

    @patch('app.lambda.s3_client.get_object')
    @patch('app.lambda.LOG.log')
    def test_handler(self, mock_log, mock_get_object):
        mock_get_object.return_value = {
            'Body': MagicMock(read=MagicMock(return_value=b'{"status": "OK", "isTvAd": True, "vast_bucket": "test-bucket", "vast_key": "test-key", "pubid": "123", "video_extension": "mp4"}'))
        }
        event = {
            "Records": [
                {
                    "s3": {
                        "bucket": {"name": "test-bucket"},
                        "object": {"key": "test-key"}
                    }
                }
            ]
        }
        context = {}
        response = handler(event, context)
        self.assertEqual(response['statusCode'], 200)

if __name__ == '__main__':
    unittest.main()
