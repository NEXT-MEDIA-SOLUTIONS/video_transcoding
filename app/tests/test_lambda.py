import unittest
import os, sys

sys.path.append('.')
workdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
print(workdir)
sys.path.append(workdir)

from lambda_function import handler

class TestLambdaHandler(unittest.TestCase):

    def test_handler(self):
        # Define event and context
        event = {
            "Records": [
                {
                    "s3": {
                        "bucket": {"name": "rmcbfmads-creatives"},
                        # "object": {"key": "inputs/jsons/archive/FR_IPNT_BRIV_BLAC_0004_020_F.json"}
                        "object": {"key": "inputs/jsons/archive/FR_LAKI_ICME_ICME_0003_030_F.json"}
                    }
                }
            ]
        }
        context = {}

        # Call the handler
        response = handler(event, context)

        # Assertions
        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(response['body'][0]['message'], 'Transcoding Pass')

if __name__ == '__main__':
    unittest.main()
