#!/usr/bin/env python
# coding: utf-8

__author__ = "Mohammed EL-KHOU"
__copyright__ = "Altice Media"
__license__ = "DWH"
__service__ = "Video Checker & Encoder"
__version__ = "1.0"

import os, sys, re
import stat
import json
import requests
from datetime import datetime, timedelta, timezone
from dateutil.relativedelta import relativedelta
import boto3
from botocore.exceptions import ClientError
import xml.etree.ElementTree as ET
from glob import glob

if __package__ is None:
    sys.path.append('.')
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.helpers.env import Env
from src.helpers.log import LOG
from src.helpers.utils import get_error_traceback, exec_cmd
from src.core.mediainfo import VideoInfo
from src.db.athena import AthenaDB
from src.tools.sftp import sftp_transfer

ENCODED_VIDEO_DIR = Env.get("ENCODED_VIDEO_DIR","/tmp/encoded_video/")
SIMPLES_VIDEO_DIR = Env.get("SIMPLES_VIDEO_DIR","/tmp/simples_video/")
os.makedirs(ENCODED_VIDEO_DIR, exist_ok=True)
os.makedirs(SIMPLES_VIDEO_DIR, exist_ok=True)

TIMEOUT = int(Env.get('TIMEOUT', 5000))

BTVS_VIDEO_KEY=Env.get("BTVS_VIDEO_KEY")
BTVS_XML_KEY=Env.get("BTVS_XML_KEY")

VIDEO_PREFIX = "pubid_"
VIDEO_BUCKET = Env.get("VIDEO_BUCKET","rmcbfmads-creatives")

# Create a timezone offset of +01:00
offset = timezone(timedelta(hours=1))
# Get the current datetime with timezone
now = datetime.now(offset)

s3_client = boto3.client('s3')


FFMPEG_DIR_PATH=Env.get("FFMPEG_DIR_PATH","/tmp/ffmpeg/")
FFMPEG_BINARY=os.path.join(FFMPEG_DIR_PATH, "ffmpeg")
os.environ["PATH"] += os.pathsep + FFMPEG_DIR_PATH

# def download_ffmpeg():
#     if not os.path.isfile(FFMPEG_BINARY):
#         os.makedirs(FFMPEG_DIR_PATH, exist_ok=True)
#         with open(FFMPEG_BINARY, 'wb') as file_obj:
#             s3_client.download_fileobj("amac-adressable-tv", "assets/ffmpeg", file_obj)
        
#         # Change permissions to make it executable
#         os.chmod(FFMPEG_BINARY, stat.S_IEXEC)

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

class Encoder:
    def __init__(self, info, video_path) -> None:
        self.info = info
        self.pub_id = info["pubid"]
        self.expected_duration = info["expected_duration"]
        self.original_video_info = None
        self.incorect_frame_count=None
        self.resolution_scale = False
        self.frame_accuracy_ok = True
        self.input_file_path = video_path
        self.output_file_path = os.path.join(ENCODED_VIDEO_DIR, self.pub_id + ".mxf")
        self.output_xml_path = os.path.join(ENCODED_VIDEO_DIR, self.pub_id + ".xml")
        self.video_btvs_url = None
        self.btvs_xml_url = None
        self.btvs_video_info=None
        self.status = "success"
        self.error_msg=""
        if os.path.isfile(self.output_file_path):
            os.remove(self.output_file_path)
        if os.path.isfile(self.output_xml_path):
            os.remove(self.output_xml_path)

    def assure(self):
        try:
            if not self.check_duration():
                return self.get_report("Verify frame accuracy KO, check the log.")
            
            self.original_video_info = VideoInfo(self.input_file_path)
            
            self.incorect_frame_count = self.original_video_info.check_frame_accuracy(self.expected_duration)
            if self.incorect_frame_count==0:
                self.frame_accuracy_ok=True
            elif abs(self.incorect_frame_count)<=5:
                self.frame_accuracy_ok=False
                LOG.log().warning(f"Verify frame accuracy KO,; incorect_frame_count : {self.incorect_frame_count}")
            else:
                return self.get_report(f"Verify frame accuracy KO, incorect_frame_count={self.incorect_frame_count}<=5")
            
            if not self.validate(self.original_video_info):
                LOG.log(name="VideoValidator").info("input_video is incorrect KO, rencoding ...")
                if self.convert() :
                    LOG.log(name="VideoValidator").info("rencoding DONE")
                    self.btvs_video_info = VideoInfo(self.output_file_path)
                    if self.validate(self.btvs_video_info):
                        LOG.log(name="VideoValidator").info("output_video is correct OK")
                        self.status = "success"
                        self.error_msg=""
                    else:
                        LOG.log(name="VideoValidator").warning("output_video is incorrect KO")
                        os.remove(self.output_file_path)
                        return self.get_report("Encoded output_video is incorrect !! skip.")
            else:
                LOG.log(name="VideoValidator").info("input_video is correct OK")
            
            self.create_xml()
            
            self.video_btvs_url = upload_to_s3(path=self.output_file_path, key_dir=BTVS_VIDEO_KEY, bucket_name=VIDEO_BUCKET)
            self.btvs_xml_url = upload_to_s3(path=self.output_xml_path, key_dir=BTVS_XML_KEY, bucket_name=VIDEO_BUCKET)

            # TODO
            if sftp_transfer(self.output_file_path):
                if sftp_transfer(self.output_xml_path):
                    return self.get_report()
            return self.get_report("Failed to transfert via SFTP !")
            # TODO
        except Exception as e:
            err_msg = get_error_traceback(e)
            LOG.log(name=__service__).critical(err_msg)
            LOG.log(name=__service__).exception('Got exception on main handler')
            return self.get_report(err_msg)

    def get_report(self, msg=None) -> dict:
        if msg is not None:
            LOG.log(name=__service__).error(msg)
            self.error_msg += "\n"+msg
            self.status = "error"
        for file in glob(os.path.join(ENCODED_VIDEO_DIR,"*"))+glob(os.path.join(SIMPLES_VIDEO_DIR,"*")):
            os.remove(file)
        return self.to_dict()

    def to_dict(self) -> dict:
        return {
            "pub_id":self.pub_id,
            "vast":{
                "bucket": self.info["vast_bucket"],
                "key" :self.info["vast_key"],
                "url": self.info["vast_url"],
            },
            "video": {
                "original_url": self.info["public_video_url"],
                "btvs_url": self.video_btvs_url,
                "btvs_xml_url": self.btvs_xml_url
            },
            "error":str(self.error_msg).strip(),
            "status":self.status
        }

    def check_duration(self) -> bool:
        reasonable_duration= self.expected_duration
        flag = 0
        flag += self.check_and_log("duration", 2*60, reasonable_duration, "<=")
        flag += self.check_and_log("duration", [15, 20, 30], reasonable_duration, "in")
        if flag!=0:
            msg=f"Video duration does not meet the standards. The video will be skipped, and no VAST will be generated !!"
            self.error_msg += "\n"+msg
            LOG.log(__service__).error(msg)
            self.status = "duration ko"
            return False
        return True
        
    def validate(self, video_info: VideoInfo) -> bool:
        self.error_msg=""
        if not self.check_duration():
            return False
        
        self.frame_accuracy_ok = video_info.check_frame_accuracy(self.expected_duration)==0
        
        self.format_ok = self.check_format(video_info.probe)
        self.video_ok = self.check_video(video_info.video_stream, video_info.video_info)
        self.audio_ok = self.check_audio(video_info.audio_streams, video_info.audio_info)
        self.loudness_ok = self.check_loudness(video_info.loudness)
        
        LOG.log(name=__service__).info(f"format_ok: {self.format_ok}, video_ok: {self.video_ok}, audio_ok: {self.audio_ok}, loudness_ok: {self.loudness_ok}, frame_accuracy_ok: {self.frame_accuracy_ok}")
        return self.format_ok and self.video_ok and self.audio_ok and self.loudness_ok and self.frame_accuracy_ok 

    def check_format(self, probe) -> bool:
        flag = 0
        flag += self.check_and_log("format_name", 'mxf', probe["format"]['format_name'])
        flag += self.check_and_log("format_long_name", "MXF (Material eXchange Format)", probe["format"]['format_long_name'])
        flag += self.check_and_log("start_time", 0.0, float(probe["format"]["start_time"]))
        flag += self.check_and_log("duration", 2*60, float(probe["format"]["duration"]), "<=")
        
        return flag==0
    
    def check_video(self, video_stream, video_info) -> bool:
        flag = 0
        flag += self.check_and_log("video width", 1920, video_stream['width'])
        self.resolution_scale = video_stream['width'] * video_stream['height'] < 1920 * 1080
        self.resolution_scale=video_stream['width']*video_stream['height'] < 1920*1080
        if "display_aspect_ratio" in video_stream:
            flag += self.check_and_log("video display_aspect_ratio", ["1.778", "16:9"], video_stream["display_aspect_ratio"], "in")
        # elif "display_aspect_ratio" in video_info:
        else:
            flag += self.check_and_log("video display_aspect_ratio", ["1.778", "16:9"], video_info["display_aspect_ratio"], "in")
        flag += self.check_and_log("video frame_rate (FPS)", 25, float(video_stream['r_frame_rate'].split('/')[0]) / float(video_stream['r_frame_rate'].split('/')[1]))
        flag += self.check_and_log("video codec_long_name", "MPEG-2 video", video_stream["codec_long_name"])
        flag += self.check_and_log("video profile", ["4:2:2", "high422"], video_stream["profile"].lower(), "in") #'422P@HL' To verify that the output video uses the 4:2:2 chroma subsampling profil
        flag += self.check_and_log("video pix_fmt", "yuv422p", video_stream["pix_fmt"]) # if you want to check specifically for the chroma subsampling format used in the video, you can use ffprobe to show the pixel format, which indirectly indicates the chroma subsampling
        if "bit_rate" in video_stream:
            flag += self.check_and_log("video bit_rate", 50000000, video_stream['bit_rate'])
        elif "bit_rate" in video_info:
            flag += self.check_and_log("video bit_rate", 50000000, video_info['bit_rate'])
        flag += self.check_and_log("video start_time", 0.0, float(video_stream["start_time"]))
        flag += self.check_and_log("video duration", 2*60, float(video_stream["duration"]), "<=")
        
        flag += self.check_and_log("video disposition lyrics", 0, int(video_stream["disposition"]["lyrics"]))#>> FRA : Renseigne la présence de sous-titrage brûlé à l’image dans la vidéo source.
        return flag==0
        
    def check_audio(self, audio_streams, audio_info) -> bool:
        flag = 0
        for i, audio_stream in enumerate(audio_streams):
            if not audio_stream :
                flag+=1
                continue
            flag += self.check_and_log(f"audio[{i}] channels", [2, 6], int(audio_stream['channels']), "in")
            flag += self.check_and_log(f"audio[{i}] sample_rate", 48000, int(audio_stream['sample_rate']))
            flag += self.check_and_log(f"audio[{i}] codec_name", 'pcm_s24le', audio_stream['codec_name'])
            flag += self.check_and_log(f"audio[{i}] bits_per_sample", 24, int(audio_stream['bits_per_sample']))
            
            flag += self.check_and_log(f"audio[{i}] start_time", 0.0, float(audio_stream["start_time"]))
            flag += self.check_and_log(f"audio[{i}] duration", 2*60, float(audio_stream["duration"]), "<=")
        return flag==0

    def check_loudness(self, loudness) -> bool:
        flag=0
        flag += self.check_and_log(f"audio integrated_loudness", -23, loudness["integrated_loudness"], "<=")
        flag += self.check_and_log(f"audio max_short-term_loudness", -20, loudness["max_short-term_loudness"], "<=")
        flag += self.check_and_log(f"audio true_peak", -3, loudness["true_peak"], "<=")
        self.check_and_log(f"audio loudness_range", 5.0, loudness["loudness_range"], ">=")
        return flag==0
    
    def check_and_log(self, key, expected, received, operator="==") -> int:
        operators = {
            ">": lambda x, y: x > y,
            "<": lambda x, y: x < y,
            ">=": lambda x, y: x >= y,
            "<=": lambda x, y: x <= y,
            "==": lambda x, y: x == y,
            "!=": lambda x, y: x != y,
            "in": lambda x, y: x in y,
        }

        if operator not in operators:
            LOG.log(name=__service__).critical(f"Invalid operator: {operator}")
            exit(1)

        if not operators[operator](received, expected):
            msg = f"{key} mismatch - expected : ({operator}) `{expected}` but received : `{received}` !"
            LOG.log(name=__service__).warning(msg)
            self.error_msg += "\n"+msg
            self.status = "check_ko"
            return 1
        return 0
    
    
    def convert(self) -> bool:
        # Convert video to the specified format
        """
        Convert the video to the specified format.
        
        -i : input file
        -f : output format
        -s  : set frame size 
        -r : Set frame rate (Hz value, fraction or abbreviation)
        -aspect : Set the video display aspect ratio specified
        -c:v : -codec:v : -vcodec : Set the video codec
        -pix_fmt : Set pixel format
        
        """
            
        loudness_conf = ""
        if not self.loudness_ok:
            cmd=f'{FFMPEG_DIR_PATH}ffmpeg -i "{self.input_file_path}" -af loudnorm=I=-24:LRA=7:tp=-3:print_format=json -f null - '
            flag, _, stderr = exec_cmd(cmd)
            if flag and stderr is not None :
                # Extract the JSON part from the output
                json_output = stderr.split('[Parsed_loudnorm_0 @')[1].strip().split("]")[1]
                json_output = json_output[:json_output.rfind('}') + 1]
                # Load the JSON data
                json_data = json.loads(json_output)
                print(json_data)
                
                loudness_conf = f""" -af "loudnorm=I=-24:LRA=7:tp=-3:measured_i={json_data['input_i']}:measured_lra={json_data['input_lra']}:measured_tp={json_data['input_tp']}:measured_thresh={json_data['input_thresh']}:offset={json_data['target_offset']}" """
        
        #To cut a video using `ffmpeg` and remove any extra milliseconds in the end, you can use the `-ss` and `-t` options to specify the start time and duration of the output video.
        duration_cuter_conf = ""
        if self.expected_duration != 0:
            LOG.log(name=__service__).warning(f"There is extra milliseconds in the end; duration:{self.expected_duration}")
            minutes, seconds = divmod(int(self.expected_duration), 60)
            duration_cuter_conf = f"-ss 00:00:00.000 -t 00:{minutes:02d}:{seconds:02d}.000" 
            
        cmd =f"""{FFMPEG_DIR_PATH}ffmpeg 
        -i "{self.input_file_path}" 
        -f mxf -map 0:v -map 0:a
        -c:v mpeg2video -pix_fmt yuv422p -profile:v 0
        -s 1920x1080 -vf "scale=1920:1080" -aspect 16:9 -r 25 -g 12 
        -b:v 50M -minrate 50M -maxrate 50M -bufsize 50M
        -c:a pcm_s24le -ar 48000 -ac 2
        {loudness_conf}
        {duration_cuter_conf}
        -y "{self.output_file_path}" """

        print(cmd.replace("\n", "\\\n"))
        flag, _, _ = exec_cmd(str(cmd).replace("\n", " "))
        if flag:
            print(f"Video converted and saved as {self.output_file_path}")
            return True
        return False
      
    def create_xml(self) -> None:
        id_ = AthenaDB.get_next_id(self.pub_id)
        # content_id=f"AMAC00000000001"
        content_id=f"AMAC{id_:010d}"
        content_name="UNI_PUB"
        content_name=content_id
        res = AthenaDB.insert_btvs_ids(id_, content_id, self.pub_id)
        print(res)
            
        text="pubid_"+self.pub_id
        # Format the datetime object to the specified format
        start_time=now.strftime("%Y-%m-%dT%H:%M:%S%z") # "2023-02-28T00:00:00+01:00"
        # Replace the last two characters to add a colon in the timezone part
        start_time = start_time[:-2] + ':' + start_time[-2:]
        end_time=(now + relativedelta(months=6)).strftime("%Y-%m-%dT%H:%M:%S%z")
        end_time = end_time[:-2] + ':' + end_time[-2:]

        hours, remainder = divmod(self.expected_duration, 3600)
        minutes, seconds = divmod(remainder, 60)
        duration = f"PT{int(hours):02d}H{int(minutes):02d}M{int(seconds):02d}S"
        mode = "INIT" #"UPDATE"
        with open(self.output_xml_path, "w", encoding="utf8") as f:
            f.write(f"""
<?xml version="1.0" encoding="utf-8" standalone="no"?>
<PCCAD_GRID xmlns:PCCAD_AD="urn:PCCAD:AD:schema" xmlns:PCCAD_CD="urn:PCCAD:CD:schema"
  xmlns:PCCAD_TV="urn:PCCAD:TVLocation:schema" xmlns:PCCAD_gc="urn:PCCAD:GC:schema"
  xmlns:PCCAD_st="urn:PCCAD:ST:schema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  action="{mode}" name="{self.pub_id}" priority="false" schemaVersion="2.5" xmlAutoProvisioning="true"
  xsi:noNamespaceSchemaLocation="SchemaW3CPCCAD_SC.xsd">
  <ContentTable>
    <PCCAD_CD:Content contentID="{content_id}" contentName="{content_name}" voLanguage="FRA">
      <PCCAD_CD:ContentDescription>
        <PCCAD_CD:Title>
          <PCCAD_CD:ShortTitle></PCCAD_CD:ShortTitle>
          <PCCAD_CD:Value>{self.pub_id}</PCCAD_CD:Value>
        </PCCAD_CD:Title>
        <PCCAD_CD:Summary>
          <PCCAD_CD:ShortSummary>{text}</PCCAD_CD:ShortSummary>
        </PCCAD_CD:Summary>
        <PCCAD_CD:Comment />
        <PCCAD_CD:Keywords>
          <PCCAD_CD:Keyword>AMAC</PCCAD_CD:Keyword>
        </PCCAD_CD:Keywords>
        <PCCAD_CD:ProductionNationality>France</PCCAD_CD:ProductionNationality>
      </PCCAD_CD:ContentDescription>
      <PCCAD_CD:ProductionDate>{datetime.now().year}</PCCAD_CD:ProductionDate>
      <PCCAD_CD:AdCreativeInfo>
        <PCCAD_CD:AdContentProvider>UNI_PUB</PCCAD_CD:AdContentProvider>
        <PCCAD_CD:ContentProviderAdId>{self.pub_id}</PCCAD_CD:ContentProviderAdId>
        <PCCAD_CD:AvisArpp>true</PCCAD_CD:AvisArpp>
        <PCCAD_CD:UniversalAdId idRegistry="arpp.org">{self.pub_id}</PCCAD_CD:UniversalAdId>
        <PCCAD_CD:EditorialDuration>{duration}</PCCAD_CD:EditorialDuration>
      </PCCAD_CD:AdCreativeInfo>
      <PCCAD_CD:GenreList />
      <PCCAD_CD:ParentalGuidance CSA="CSA_1" />
    </PCCAD_CD:Content>
  </ContentTable>
  <ContentLocationTable>
    <ADContentLocation>
      <PCCAD_AD:ContentProvider name="UNI_PUB" />
      <PCCAD_AD:Instructions>
        <PCCAD_AD:DateExpiration xmlns:PCCAD_cl="urn:PCCAD:CL:schema">{end_time}</PCCAD_AD:DateExpiration>
        <PCCAD_AD:AdminValidation>false</PCCAD_AD:AdminValidation>
        <PCCAD_AD:DisplayMode xmlns:PCCAD_cl="urn:PCCAD:CL:schema" serviceName="STREAMING">
          <PCCAD_AD:AvailableStartDate>{start_time}</PCCAD_AD:AvailableStartDate>
          <PCCAD_AD:AvailableEndDate>{end_time}</PCCAD_AD:AvailableEndDate>
        </PCCAD_AD:DisplayMode>
        <PCCAD_AD:AllowTerminal>ALL</PCCAD_AD:AllowTerminal>
      </PCCAD_AD:Instructions>
      <PCCAD_AD:AVAttributes>
        <PCCAD_CD:VideoAttributes aspectRatio="16:9" videoDefinition="HD" videoFormat="MPEG2" />
        <PCCAD_CD:AudioAttributes>
          <PCCAD_CD:AudioTrack xmlns:PCCAD_cl="urn:PCCAD:CL:schema" channelNumber="2.0"
            language="FRA" order="0" />
        </PCCAD_CD:AudioAttributes>
        <PCCAD_CD:MediaAttributes>
          <PCCAD_CD:MediaTrack>
            <PCCAD_CD:SubTitleInVideo>FRA</PCCAD_CD:SubTitleInVideo>
          </PCCAD_CD:MediaTrack>
        </PCCAD_CD:MediaAttributes>
        <PCCAD_AD:OriginalFilename>{self.pub_id}.mxf</PCCAD_AD:OriginalFilename>
        <PCCAD_AD:SourceBitRate>50000000</PCCAD_AD:SourceBitRate>
        <PCCAD_AD:Duration>{duration}</PCCAD_AD:Duration>
      </PCCAD_AD:AVAttributes>
    </ADContentLocation>
  </ContentLocationTable>
</PCCAD_GRID>
""")