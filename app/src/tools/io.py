#!/usr/bin/env python
# coding: utf-8

__author__ = "Mohammed EL-KHOU"
__copyright__ = "Altice Media"
__license__ = "DWH"
__service__ = "Lambda Video Encoder"
__version__ = "1.0"

import os
import sys
import requests
import boto3

if __package__ is None:
    sys.path.append('.')
    workdir=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.append(workdir)

from src.helpers.log import LOG
from src.helpers.utils import get_error_traceback

# Initialize S3 client
s3_client = boto3.client('s3')


# def download_file_from_url(url, path):
#     response = requests.get(url)
#     if response.status_code == 200:
#         with open(path, "wb") as f:
#             f.write(response.content)
#         return True
#     return False


def download_file_from_url(url: str, destination_path: str) -> bool:
    """
    Downloads a file from the specified URL and saves it to the given file path.

    Args:
        url (str): The URL of the file to download.
        destination_path (str): The local file path where the downloaded file should be saved.

    Returns:
        bool: True if the file was downloaded and saved successfully, False otherwise.

    Raises:
        requests.exceptions.RequestException: If there is an issue with the HTTP request.

    Example:
        >>> download_file_from_url("https://example.com/file.txt", "./file.txt")
        True
    """
    try:
        response = requests.get(url, timeout=6*60)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)

        with open(destination_path, "wb") as file:
            file.write(response.content)

        return True
    except requests.exceptions.RequestException as e:
        print(f"Error downloading file: {e}")
        return False

def download_video_from_s3(bucket_name: str, object_key: str, local_file_path: str) -> bool:
    """
    Download a video file from S3 to a local path.

    Args:
        bucket_name (str): The name of the S3 bucket.
        object_key (str): The key of the object in the S3 bucket.
        local_file_path (str): The local path to save the downloaded file.

    Returns:
        bool: True if download was successful, False otherwise.
    """
    try:
        with open(local_file_path, 'wb') as file_obj:
            s3_client.download_fileobj(bucket_name, object_key, file_obj)
        LOG.log(__service__).info(f"Successfully downloaded {object_key} from {bucket_name} to {local_file_path}")
        return True
    except Exception as e:
        LOG.log(__service__).error(f"Error downloading file: {get_error_traceback(e)}")
        return False
    
def upload_to_s3(key_dir=None, path=None, file_key=None, bucket_name=None, is_public=True):
    if file_key is None:
        # Upload the converted file to S3
        file_key= os.path.join(key_dir, path.replace("\\", "/").split("/")[-1]).replace("\\", "/")
    if is_public:
        s3_client.upload_file(path, bucket_name, file_key, ExtraArgs={'ACL': 'public-read'})
    else:
        s3_client.upload_file(path, bucket_name, file_key)
    # Construct the public URL
    public_url = f'https://{bucket_name}.s3.amazonaws.com/{file_key}'
    return public_url