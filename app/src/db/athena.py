#!/usr/bin/env python
# coding: utf-8

__author__ = "Mohammed EL-KHOU"
__copyright__ = "Altice Media"
__license__ = "DWH"
__service__ = "Athena DataBase"
__version__ = "1.0"

import warnings
from sqlalchemy import exc as sa_exc
# Filter out all SQLAlchemy warnings
warnings.filterwarnings('ignore', category=sa_exc.SADeprecationWarning)

import os, sys, time
from sqlalchemy import create_engine
import pandas as pd
import boto3

if __package__ is None:
    sys.path.append('.')
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.helpers.env import Env
from src.helpers.log import LOG
from src.helpers.utils import get_error_traceback

AWS_DEFAULT_REGION=Env.get("AWS_DEFAULT_REGION")
DB_ATHENA_S3_STAGING_DIR=Env.get("DB_ATHENA_S3_STAGING_DIR")
AWS_ACCESS_KEY_ID=Env.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY=Env.get("AWS_SECRET_ACCESS_KEY")
DB_ATHENA_ENGINE_PATH_WIN_AUTH=Env.get("DB_ATHENA_ENGINE_PATH_WIN_AUTH")
log_flag = Env.get('APP_LOG')=='true'
global_nb_try=int(Env.get("TOTALE_CONTROLE",6))
sleep_time=int(Env.get("SLEEP_TIME",5))

boto3.setup_default_session(region_name=AWS_DEFAULT_REGION)

class AthenaDB:
    _client = None
    _engine = None
    _session = None

    @staticmethod
    def get_client():
        """ Méthode statique pour récupérer l'instance unique de la classe """
        if AthenaDB._client is None:
            AthenaDB._client = boto3.client(
                'athena', 
                aws_access_key_id=AWS_ACCESS_KEY_ID, 
                aws_secret_access_key=AWS_SECRET_ACCESS_KEY, 
                region_name=AWS_DEFAULT_REGION)
        return AthenaDB._client
    
    @staticmethod
    def table_exists(database_name, table_name):
        client = AthenaDB.get_client()
        try:
            response = client.get_table_metadata(
                CatalogName='AwsDataCatalog',
                DatabaseName=database_name,
                TableName=table_name
            )
            return True
        except client.exceptions.MetadataException:
            return False

    @staticmethod
    def run_query(query):
        """ Méthode pour exécuter une requête """
        response = AthenaDB.get_client().start_query_execution(
            QueryString=query,
            # QueryExecutionContext={'Database': self.database},
            ResultConfiguration={'OutputLocation': DB_ATHENA_S3_STAGING_DIR}
        )
        # Get the query execution ID
        query_execution_id = response['QueryExecutionId']
        # Check the status of the query execution
        query_status = None
        while query_status in (None, 'QUEUED', 'RUNNING'):
            response = AthenaDB.get_client().get_query_execution(QueryExecutionId=query_execution_id)
            query_status = response['QueryExecution']['Status']['State']
            if query_status in ['QUEUED', 'RUNNING']:
                print('Query still running...')
                time.sleep(0.5)
            else:
                print('Query finished!')

        # Once the query is finished, retrieve the results
        if query_status == 'SUCCEEDED':
            results_response = AthenaDB.get_client().get_query_results(QueryExecutionId=query_execution_id)
            return results_response['ResultSet']['Rows']
        return None

    @staticmethod
    def get_engine():
        if AthenaDB._engine is None:
            # Create an SQLAlchemy engine to connect to AthenaDB
            AthenaDB._engine = create_engine(DB_ATHENA_ENGINE_PATH_WIN_AUTH)
        return AthenaDB._engine
    
    @staticmethod
    def get_session():
        if AthenaDB._session is None:
        #     Session = sessionmaker(bind=AthenaDB.get_engine())
        #     AthenaDB._session = Session()
        # return AthenaDB._session
            AthenaDB._session = boto3.Session(
                aws_access_key_id=AWS_ACCESS_KEY_ID, 
                aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                region_name=AWS_DEFAULT_REGION)
        return AthenaDB._session
    
    @staticmethod
    def reset():
        try:
            AthenaDB._session.close()
        except: pass
        AthenaDB._client = None
        AthenaDB._engine = None
        AthenaDB._session = None
        time.sleep(sleep_time)

    @staticmethod
    def select_query(query=None):
        nb_try=global_nb_try
        err_msg=""
        while nb_try>=0:
            try:
                df = pd.read_sql(query, AthenaDB.get_engine())
                return df
            except Exception as e:
                err_msg=f"Failed to fetch query: '{query}' with Exception: {get_error_traceback(e)} !!"
                if log_flag: LOG.log(__service__).error(err_msg)
                nb_try-=1
                AthenaDB.reset()
        return err_msg

    @staticmethod
    def get_next_id(pub_id=None):
        query=f"""
        SELECT COALESCE(
            (SELECT id FROM provisioning.btvs_ids WHERE pub_id = '{pub_id}' ORDER BY add_at DESC LIMIT 1),
            (SELECT COALESCE(MAX(id), 0) + 1 FROM provisioning.btvs_ids)
        ) AS next_id"""
        df = pd.read_sql(query, AthenaDB.get_engine())
        if "next_id" in df.columns:
            return df.loc[0, "next_id"]
        return None

    @staticmethod
    def insert_btvs_ids(id, content_id, pub_id):
        query=f"""
        INSERT INTO provisioning.btvs_ids (id, content_id, pub_id, add_at)
        VALUES ({id}, '{content_id}', '{pub_id}', current_timestamp);
        """
        return AthenaDB.run_query(query)

if __name__ == "__main__":
    # print(AthenaDB.insert_btvs_ids("0", "test0", "test0"))
    # print(AthenaDB.get_next_id())

    # Execute the query
    query = "select * from commercial.audio where cast(date as date) >= date_add('month',-2, cast(current_date as date));"
    df = AthenaDB.select_query(query)
    # Display the query results
    print(df)
