#!/usr/bin/env python
# coding: utf-8

__author__ = "Mohammed EL-KHOU"
__copyright__ = "Altice Media"
__license__ = "DWH"
__service__ = "MediaInfo"
__version__ = "1.0"

import os, sys, json, re
import subprocess as sp
import cv2
from typing import Dict, Optional, Any

if __package__ is None:
    sys.path.append('.')
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.helpers.env import Env
from src.helpers.log import LOG
from src.helpers.utils import get_error_traceback, exec_cmd

FFMPEG_DIR_PATH= Env.get("FFMPEG_DIR_PATH","")
os.environ["PATH"] += os.pathsep + FFMPEG_DIR_PATH

# import ffmpeg
import pydub
if FFMPEG_DIR_PATH != "":
    pydub.AudioSegment.converter = os.path.join(FFMPEG_DIR_PATH,'ffmpeg')
from pydub import AudioSegment
from pymediainfo import MediaInfo

class VideoInfo:

    def __init__(self, file_path):
        LOG.log(name=__service__).info("Extracting video info [START]")
        self.file_path = file_path
        
        self.file_size = os.stat(file_path).st_size
        self.loudness = self.get_loudness()
        self.probe = self.get_video_properties()

        self.video_stream = next((stream for stream in self.probe['streams'] if stream['codec_type'] == 'video'), None)
        self.video_stream["frame_rate"] = float(self.video_stream['r_frame_rate'].split('/')[0]) / float(self.video_stream['r_frame_rate'].split('/')[1])
        
        self.audio_streams = [stream for stream in self.probe['streams'] if stream['codec_type'] == 'audio']
        self.video_info, self.audio_info = self.get_media_info()

        LOG.log(name=__service__).info("Extracting video info [DONE]")

    def check_frame_accuracy(self, expected_duration) -> int:
        LOG.log(name=__service__).info("Check frame accuracy [START]")
        frame_count = None
        frame_rate = None
        if "frame_count" in self.video_stream and "frame_rate" in self.video_stream:
            frame_count = float(self.video_stream["frame_count"])
            frame_rate = float(self.video_stream["frame_rate"])
        elif 'frame_count' in self.video_info and 'frame_rate' in self.video_info:
            frame_rate = self.video_info['frame_rate']
            frame_count = self.video_info['frame_count']
        else:
            # Load the video file
            cap = cv2.VideoCapture(self.file_path)
            frame_count = float(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            frame_rate = cap.get(cv2.CAP_PROP_FPS)
            
            # Use ffprobe to get frame count and frame rate
            # cmd = f'{FFMPEG_DIR_PATH}ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames,r_frame_rate -of csv=p=0 "{self.file_path}"'
            # flag, stdout, _ = exec_cmd(cmd)
            # if flag and stdout:
            #     frame_count, r_frame_rate = stdout.strip().split(',')
            #     frame_count = float(frame_count)
            #     num, den = map(int, r_frame_rate.split('/'))
            #     frame_rate = num / den
            # else:
            #     LOG.log(name=__service__).error("Failed to get frame count and frame rate")
            #     return None

        LOG.log(name=__service__).info(f"frame_count: {frame_count}, frame_rate: {frame_rate}")
        estimated_duration = frame_count / frame_rate
        LOG.log(name=__service__).info(f"estimated_duration: {estimated_duration}, expected_duration: {expected_duration}")
        
        expected_frame_count = expected_duration * frame_rate
        incorect_frame_count = frame_count - expected_frame_count
        
        LOG.log(name=__service__).info(f"frame_count: {frame_count}, expected_frame_count: {expected_frame_count}, incorect_frame_count: {incorect_frame_count}")
    
        LOG.log(name=__service__).info("Check frame accuracy [DONE]")
        return incorect_frame_count
        
    def get_video_properties(self):
        # probe = ffmpeg.probe(self.file_path)
        cmd=f'{FFMPEG_DIR_PATH}ffprobe -show_format -show_streams -of json -v error "{self.file_path}"'
        flag, stdout, _ = exec_cmd(cmd)
        if flag and stdout is not None :
            return json.loads(stdout)
        return None

    def get_media_info(self):
        media_info = MediaInfo.parse(self.file_path) 
        # print(json.dumps(media_info.to_data(), indent=4))
        video_info = {}
        audio_info = {}
        
        for track in media_info.tracks:
            # print(track)
            if track.track_type == 'Video':
                video_info['codec'] = track.codec_id
                video_info['width'] = track.width
                video_info['height'] = track.height
                video_info['frame_rate'] = float(track.frame_rate)
                video_info['frame_count'] = float(track.frame_count)
                video_info['bit_depth'] = track.bit_depth
                video_info['bit_rate'] = track.bit_rate
                video_info["display_aspect_ratio"] = track.display_aspect_ratio
            elif track.track_type == 'Audio':
                audio_info['codec'] = track.codec_id
                audio_info['channels'] = track.channel_s
                audio_info['sample_rate'] = track.sampling_rate
                audio_info['bit_depth'] = track.bit_depth

        return video_info, audio_info

    def get_duration(self):
        """Get duration of the video file
        Cette méthode utilise ffprobe, un outil qui fait partie du paquetage ffmpeg, 
        pour extraire la durée de la vidéo directement à partir des métadonnées du fichier vidéo.
        """
        cmd = [
            f"{FFMPEG_DIR_PATH}ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            self.file_path
        ]

        flag, stdout, _ = exec_cmd(" ".join(cmd))
        if flag and stdout is not None :
            return float(stdout)
        return None

    def get_segment_duration(self):
        audio = AudioSegment.from_file(self.file_path)
        duration = audio.duration_seconds
        return duration

    def get_loudness(self):
        LOG.log(name=__service__).info("Get Audio loudness using ffmpeg [START]")
        try:
            command = [
                f"{FFMPEG_DIR_PATH}ffmpeg",
                "-i", self.file_path,
                "-af", "ebur128=peak=true",
                "-f", "null",
                "-"
            ]
            result = sp.run(command, capture_output=True, text=True, check=True)
            # Extracting Max True Peak Level from FFmpeg output
            output_lines = result.stderr.split("Summary:")[-1].strip().split('\n')
            res = {}
            for line in output_lines:
                if "I:" in line:
                    res["integrated_loudness"] = float(line.split('I:')[1].strip().split(' ')[0])
                elif 'LRA:' in line:
                    res["loudness_range"] = float(line.split('LRA:')[1].strip().split(' ')[0])
                elif 'LRA high:' in line: # The short-term loudness is typically the high LRA value
                    res["max_short-term_loudness"] = float(line.split('LRA high:')[1].strip().split(' ')[0])
                elif 'LRA low:' in line: 
                    res["min_short-term_loudness"] = float(line.split('LRA low:')[1].strip().split(' ')[0])
                elif 'Peak:' in line:
                    res["true_peak"] = float(line.split('Peak:')[1].strip().split(' ')[0])
                if "max_short-term_loudness" in res and "min_short-term_loudness" in res:
                    res["short-term_loudness_range"] = res["max_short-term_loudness"] - res["min_short-term_loudness"]
            LOG.log(name=__service__).info("Get Audio loudness using ffmpeg [DONE]")
            return res

        except sp.CalledProcessError as e:
            LOG.log(name=__service__).error(f"Error: {get_error_traceback(e)}")
        except Exception as e:
            LOG.log(name=__service__).error(f"Unexpected error: {get_error_traceback(e)}")
        LOG.log(name=__service__).info("Get Audio loudness using ffmpeg [DONE]")
        return None

    
    def get_video_info(self) -> Optional[Dict[str, float]]:
        """
        Get video information using ffmpeg.

        Args:
            file_path (str): Path to the video file.

        Returns:
            Optional[Dict[str, float]]: Dictionary containing video information or None if an error occurred.
        """
        LOG.log(__service__).info("Get video information using ffmpeg [START]")
        try:
            command = [
                f"{FFMPEG_DIR_PATH}ffmpeg",
                "-i", self.file_path,
                "-af", "ebur128=peak=true",
                "-f", "null",
                "-"
            ]
            result = sp.run(command, capture_output=True, text=True, check=True)
            
            info = {}
            loudness_flag = False
            
            for line in result.stderr.splitlines():
                if "Duration" in line:
                    match = re.search(r"Duration: (\d{2}):(\d{2}):(\d{2})\.(\d{2})", line)
                    if match:
                        hours, minutes, seconds, milliseconds = map(int, match.groups())
                        info["duration_seconds"] = hours * 3600 + minutes * 60 + seconds + milliseconds / 100
                        
                    fps_match = re.search(r'(\d+)\s+fps', line)
                    if fps_match:
                        info["frame_rate"] = int(fps_match.group(1))
                if "bitrate" in line:
                    match = re.search(r"bitrate: (\d+) kb/s", line)
                    if match:
                        info["bitrate_kbps"] = int(match.group(1))
                elif "Stream" in line and "Video" in line:
                    width_height_match = re.search(r"(\d+)x(\d+)", line)
                    if width_height_match:
                        info["width"], info["height"] = map(int, width_height_match.groups())
                elif "Summary:" in line:
                    loudness_flag = True
                elif loudness_flag and "I:" in line:
                    info["integrated_loudness"] = float(line.split('I:')[1].strip().split(' ')[0])
                elif loudness_flag and 'LRA:' in line:
                    info["loudness_range"] = float(line.split('LRA:')[1].strip().split(' ')[0])
                elif loudness_flag and 'LRA high:' in line: # The short-term loudness is typically the high LRA value
                    info["max_short-term_loudness"] = float(line.split('LRA high:')[1].strip().split(' ')[0])
                elif loudness_flag and 'LRA low:' in line: 
                    info["min_short-term_loudness"] = float(line.split('LRA low:')[1].strip().split(' ')[0])
                elif loudness_flag and 'Peak:' in line:
                    info["true_peak"] = float(line.split('Peak:')[1].strip().split(' ')[0])
                if loudness_flag and "max_short-term_loudness" in info and "min_short-term_loudness" in info:
                    info["short-term_loudness_range"] = info["max_short-term_loudness"] - info["min_short-term_loudness"]
            
            LOG.log(__service__).info("Get video information using ffmpeg [DONE]")
            return info
        except Exception as e:
            LOG.log(__service__).error(f"Error getting video info: {get_error_traceback(e)}")
        return None