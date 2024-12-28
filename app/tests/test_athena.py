import os, sys

sys.path.append('.')
workdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
print(workdir)
sys.path.append(workdir)

import unittest
from unittest.mock import patch, MagicMock
from app.src.db.athena import AthenaDB

class TestAthenaDB(unittest.TestCase):

    @patch('app.src.db.athena.boto3.client')
    def test_get_client(self, mock_boto_client):
        mock_client_instance = MagicMock()
        mock_boto_client.return_value = mock_client_instance

        client = AthenaDB.get_client()
        self.assertEqual(client, mock_client_instance)
        mock_boto_client.assert_called_once_with(
            'athena',
            aws_access_key_id=AthenaDB.DB_ATHENA_AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AthenaDB.DB_ATHENA_AWS_SECRET_ACCESS_KEY,
            region_name=AthenaDB.DB_ATHENA_REGION_NAME
        )

    @patch('app.src.db.athena.pd.read_sql')
    @patch('app.src.db.athena.AthenaDB.get_engine')
    def test_get_next_id(self, mock_get_engine, mock_read_sql):
        mock_engine = MagicMock()
        mock_get_engine.return_value = mock_engine
        mock_df = MagicMock()
        mock_df.columns = ["next_id"]
        mock_df.loc[0, "next_id"] = 1
        mock_read_sql.return_value = mock_df

        next_id = AthenaDB.get_next_id("test_pub_id")
        self.assertEqual(next_id, 1)
        mock_read_sql.assert_called_once()
        mock_get_engine.assert_called_once()

    @patch('app.src.db.athena.AthenaDB.run_query')
    def test_insert_btvs_ids(self, mock_run_query):
        mock_run_query.return_value = "Query Result"
        result = AthenaDB.insert_btvs_ids(1, "test_content_id", "test_pub_id")
        self.assertEqual(result, "Query Result")
        mock_run_query.assert_called_once()

    @patch('app.src.db.athena.pd.read_sql')
    @patch('app.src.db.athena.AthenaDB.get_engine')
    def test_select_query(self, mock_get_engine, mock_read_sql):
        mock_engine = MagicMock()
        mock_get_engine.return_value = mock_engine
        mock_df = MagicMock()
        mock_read_sql.return_value = mock_df

        query = "SELECT * FROM test_table"
        result = AthenaDB.select_query(query)
        self.assertEqual(result, mock_df)
        mock_read_sql.assert_called_once_with(query, mock_engine)
        mock_get_engine.assert_called_once()

    @patch('app.src.db.athena.boto3.client')
    def test_run_query(self, mock_boto_client):
        mock_client_instance = MagicMock()
        mock_boto_client.return_value = mock_client_instance
        mock_client_instance.start_query_execution.return_value = {'QueryExecutionId': '123'}
        mock_client_instance.get_query_execution.side_effect = [
            {'QueryExecution': {'Status': {'State': 'RUNNING'}}},
            {'QueryExecution': {'Status': {'State': 'SUCCEEDED'}}}
        ]
        mock_client_instance.get_query_results.return_value = {'ResultSet': {'Rows': ['row1', 'row2']}}

        result = AthenaDB.run_query("SELECT * FROM test_table")
        self.assertEqual(result, ['row1', 'row2'])
        mock_client_instance.start_query_execution.assert_called_once()
        self.assertEqual(mock_client_instance.get_query_execution.call_count, 2)
        mock_client_instance.get_query_results.assert_called_once_with(QueryExecutionId='123')

if __name__ == '__main__':
    unittest.main()