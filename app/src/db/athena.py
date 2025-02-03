#!/usr/bin/env python
# coding: utf-8

__author__ = "Mohammed EL-KHOU"
__copyright__ = "Altice Media"
__license__ = "DWH"
__service__ = "Athena DataBase"
__version__ = "1.0"

import warnings
warnings.filterwarnings("ignore")
import os, sys, time
import boto3

sys.path.append('.')
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.helpers.env import Env
from src.helpers.log import LOG

USE_AWS_KEY=os.environ.get("USE_AWS_KEY", False)
AWS_ACCESS_KEY_ID=Env.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY=Env.get("AWS_SECRET_ACCESS_KEY")
AWS_DEFAULT_REGION=Env.get("AWS_DEFAULT_REGION")

DB_ATHENA_S3_STAGING_DIR=Env.get("DB_ATHENA_S3_STAGING_DIR")
log_flag = Env.get('APP_LOG')=='true'
global_nb_try=int(Env.get("TOTALE_CONTROLE",6))
sleep_time=int(Env.get("SLEEP_TIME",5))

boto3.setup_default_session(region_name=AWS_DEFAULT_REGION)

if USE_AWS_KEY in ('true',True) and AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY and AWS_DEFAULT_REGION:
    athena_client = boto3.client(
            'athena', 
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_DEFAULT_REGION)
else:
    athena_client = boto3.client('athena')

def execute_query(query, database):
    response = athena_client.start_query_execution(
        QueryString=query,
        QueryExecutionContext={'Database': database},
        ResultConfiguration={'OutputLocation': DB_ATHENA_S3_STAGING_DIR}
    )
    return response['QueryExecutionId']

def get_query_results(query_execution_id):
    while True:
        response = athena_client.get_query_execution(QueryExecutionId=query_execution_id)
        state = response['QueryExecution']['Status']['State']
        if state in ['SUCCEEDED', 'FAILED', 'CANCELLED']:
            break
        time.sleep(1)
    
    if state == 'SUCCEEDED':
        results = athena_client.get_query_results(QueryExecutionId=query_execution_id)
        return results['ResultSet']['Rows']
    else:
        raise Exception(f"Query failed with state: {state}")

def get_next_id(pub_id=None):
    # query=f"""
    # SELECT COALESCE(
    #     (SELECT id FROM provisioning.btvs_ids WHERE pub_id = '{pub_id}' ORDER BY add_at DESC LIMIT 1),
    #     (SELECT COALESCE(MAX(id), 0) + 1 FROM provisioning.btvs_ids)
    # ) AS next_id"""
    query="SELECT COALESCE(MAX(id), 0) + 1 AS next_id FROM provisioning.btvs_ids"
    select_response = execute_query(query, "provisioning")
    query_results = get_query_results(select_response)
    return int(next(row['Data'][0]['VarCharValue'] for row in query_results if row['Data'][0]['VarCharValue'] != 'next_id'))

def insert_btvs_ids(id, content_id, pub_id):
    query=f"""
    INSERT INTO provisioning.btvs_ids (id, content_id, pub_id, add_at)
    VALUES ({id}, '{content_id}', '{pub_id}', current_timestamp);
    """
    return execute_query(query, "provisioning")


if __name__ == "__main__":
    id_ = get_next_id('FR_ADFN_ODMF_ODMF_0001_020_F')
    print(id_)
    # content_id=f"AMAC00000000001"
    content_id=f"AMAC{id_:010d}"
    print(content_id)
