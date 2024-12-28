#!/usr/bin/env python
# coding: utf-8

__author__ = "Mohammed EL-KHOU"
__copyright__ = "Altice Media"
__license__ = "DWH"
__service__ = "Lambda Video Encoder"
__version__ = "1.0"

import os
import sys
import json
import time
import re
from datetime import datetime

if __package__ is None:
    sys.path.append('.')
    workdir=os.path.dirname(os.path.abspath(__file__))
    sys.path.append(workdir)

from src.helpers.env import Env
from src.helpers.log import LOG

APP_LOG_DIR = Env.get("APP_LOG_DIR")
os.makedirs(APP_LOG_DIR,exist_ok=True)
log_file_path=os.path.join(APP_LOG_DIR,f"{__service__.lower().strip().replace(' ','_')}-{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
LOG.log(name=__service__, log_file_path=log_file_path)

from src.core.btvs import Encoder
from src.tools.mail import send_mail
from src.helpers.utils import convert_seconds_to_dhms
from src.tools.io import download_file_from_url, download_video_from_s3, s3_client

def handler(event, context):
    LOG.log(__service__).info(f"🚀 {__service__} APP START 🚀")
    cycle_start_at = time.time()
    print(event)
    report=[]
    failed_count, analysed_count = 0, 0

    if "Records" in event:
        for record in event['Records']:
            bucket = str(record['s3']['bucket']['name'])
            key = str(record['s3']['object']['key'])

            response = s3_client.get_object(Bucket=bucket, Key=key)
            video_info = json.loads(response['Body'].read().decode('utf-8'))

            if video_info["error"] is not None or video_info["status"] != "OK" or video_info["isTvAd"] is False:
                continue

            response = s3_client.get_object(Bucket=video_info["vast_bucket"], Key=video_info["vast_key"])
            xml_content = re.sub(r'\s+', '',response['Body'].read().decode('utf-8'))
            if xml_content != "" and xml_content != "<VAST/>" and xml_content != "<VAST></VAST>":
                LOG.log(__service__).warning("vast xml file is not empty !")
                continue

            video_path = f"/tmp/{video_info['pubid']}.{video_info['video_extension']}"
            flag=True
            item=None
            if 'video_key_src' in video_info and 'video_bucket_src' in video_info and 'public_video_url_src' in video_info:
                if video_info["video_key_src"] is None and video_info["video_bucket_src"] is None and video_info["public_video_url_src"] is not None:
                    LOG.log().info("la source video de base est une URL externe!")
                    if not download_file_from_url(video_info["public_video_url_src"], video_path):
                        continue
                elif video_info["video_key_src"] is not None and video_info["video_bucket_src"] is not  None and video_info["public_video_url_src"] is not None:
                    LOG.log().info("la source video de base est un fichie uploder!")
                    if not download_video_from_s3(video_info["video_bucket_src"], video_info["video_key_src"], video_path):
                        continue
                else:
                    LOG.log().error("il y a un error dans le fichier de configuration , certain valeur ne sont pas corect")
                    continue
                
                # TODO
                video_validator = Encoder(video_info, video_path)
                item = video_validator.assure()
                flag = item["status"] != "success"
            if flag:
                if item is None:
                    LOG.log().error("La vidéo d'origine est respect deja la densité senore et frame accurate")
                if video_info["video_key"] is None and video_info["video_bucket"] is None and video_info["public_video_url"] is not None:
                    LOG.log().info("la source video de base est une URL externe!")
                    if not download_file_from_url(video_info["public_video_url"], video_path):
                        continue
                elif video_info["video_key"] is not None and video_info["video_bucket"] is not  None and video_info["public_video_url"] is not None:
                    LOG.log().info("la source video de base est un fichie uploder!")
                    if not download_video_from_s3(video_info["video_bucket"], video_info["video_key"], video_path):
                        continue
                else:
                    LOG.log().error("il ya un error dans le fichier de configuration , certain valeur ne sont pas corect")
                    continue
                
                # TODO

                video_validator = Encoder(video_info, video_path)
                item = video_validator.assure()
            if item["status"] == "success":
                item.update({
                    "status": "success",
                    "message": "Transcoding Pass"
                })
            else:
                item.update({
                    "status": "error",
                    "message": f"Transcoding Failed: {item['error']}"
                })
        report.append(item)
    else:
        LOG.log(__service__).info(f"❌ {__service__} APP FAILED ❌")
        
    LOG.log(__service__).info(report)
    report=json.dumps(report, indent=4)
    taking_time = int(time.time()-cycle_start_at)
    message = str(f"{__service__} APP DONE, with :\n"+
        f"""\n- 📍Processed vast: {analysed_count}"""+
        f"""\n- ‼Failed vast: {failed_count}"""+
        f"""\n- 🕑Time spent: {convert_seconds_to_dhms(taking_time)} = ({taking_time} s)"""+
        f"""\n- 📄Details: {report}""")

    LOG.log(__service__).info(f"🎯 That's all 🙏 {__service__} APP Done 🚩, see you next time 👋👋👋")
    send_mail(message_content=message,  attachment_file_path=log_file_path)
    return {
        'statusCode': 200,
        'body': report
    }
