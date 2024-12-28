#!/usr/bin/env python
# coding: utf-8
import sys, os
sys.path.append('.')
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.helpers.env import Env
from src.helpers.log import LOG
from src.helpers.utils import convert_seconds_to_dhms
from src.core.btvs import Encoder
from src.tools.mail import send_mail

l=[
("FR_THPS_MACF_MAMS_0069_015_F","https://rmcbfmads-creatives.s3.amazonaws.com/inputs/videos/FR_THPS_MACF_MAMS_0069_015_F.mp4"),
("FR_THPS_MACF_MAMS_0070_015_F","https://rmcbfmads-creatives.s3.amazonaws.com/inputs/videos/FR_THPS_MACF_MAMS_0070_015_F.mp4"),
("FR_THPS_MACF_MAMS_0067_015_F","https://rmcbfmads-creatives.s3.amazonaws.com/inputs/videos/FR_THPS_MACF_MAMS_0067_015_F.mp4"),
("FR_THPS_MACF_MAMS_0068_015_F","https://rmcbfmads-creatives.s3.amazonaws.com/inputs/videos/FR_THPS_MACF_MAMS_0068_015_F.mp4"),

]


# (info, video_path)

for pubid, url in l:
    video_validator = Encoder(
        video_url=url, 
        pub_id=pubid)
    item = video_validator.assure()
