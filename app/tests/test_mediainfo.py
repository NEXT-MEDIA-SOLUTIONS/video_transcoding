import unittest
from unittest.mock import patch, MagicMock
from src.core.mediainfo import VideoInfo

class TestVideoInfo(unittest.TestCase):

    @patch('src.core.mediainfo.os.stat')
    @patch('src.core.mediainfo.VideoInfo.get_loudness')
    @patch('src.core.mediainfo.VideoInfo.get_video_properties')
    @patch('src.core.mediainfo.VideoInfo.get_media_info')
    def setUp(self, mock_get_media_info, mock_get_video_properties, mock_get_loudness, mock_stat):
        mock_stat.return_value.st_size = 1024
        mock_get_loudness.return_value = {"integrated_loudness": -23.0}
        mock_get_video_properties.return_value = {
            'streams': [
                {'codec_type': 'video', 'r_frame_rate': '25/1'},
                {'codec_type': 'audio'}
            ]
        }
        mock_get_media_info.return_value = ({'frame_rate': 25.0, 'frame_count': 500}, {})
        self.video_info = VideoInfo("dummy_path.mp4")

    def test_init(self):
        self.assertEqual(self.video_info.file_size, 1024)
        self.assertEqual(self.video_info.loudness, {"integrated_loudness": -23.0})
        self.assertEqual(self.video_info.video_stream['frame_rate'], 25.0)
        self.assertEqual(len(self.video_info.audio_streams), 1)

    @patch('src.core.mediainfo.cv2.VideoCapture')
    def test_check_frame_accuracy(self, mock_VideoCapture):
        mock_cap = MagicMock()
        mock_cap.get.side_effect = [500.0, 25.0]
        mock_VideoCapture.return_value = mock_cap
        incorrect_frame_count = self.video_info.check_frame_accuracy(20)
        self.assertEqual(incorrect_frame_count, 0)

    @patch('src.core.mediainfo.exec_cmd')
    def test_get_video_properties(self, mock_exec_cmd):
        mock_exec_cmd.return_value = (True, '{"streams": []}', None)
        result = self.video_info.get_video_properties()
        self.assertEqual(result, {"streams": []})

    @patch('src.core.mediainfo.MediaInfo.parse')
    def test_get_media_info(self, mock_parse):
        mock_parse.return_value.tracks = [
            MagicMock(track_type='Video', codec_id='h264', width=1920, height=1080, frame_rate='25', frame_count='500', bit_depth=8, bit_rate=4000, display_aspect_ratio='16:9'),
            MagicMock(track_type='Audio', codec_id='aac', channel_s=2, sampling_rate=48000, bit_depth=16)
        ]
        video_info, audio_info = self.video_info.get_media_info()
        self.assertEqual(video_info['codec'], 'h264')
        self.assertEqual(audio_info['codec'], 'aac')

    @patch('src.core.mediainfo.exec_cmd')
    def test_get_duration(self, mock_exec_cmd):
        mock_exec_cmd.return_value = (True, '20.0', None)
        duration = self.video_info.get_duration()
        self.assertEqual(duration, 20.0)

    @patch('src.core.mediainfo.AudioSegment.from_file')
    def test_get_segment_duration(self, mock_from_file):
        mock_audio = MagicMock()
        mock_audio.duration_seconds = 20.0
        mock_from_file.return_value = mock_audio
        duration = self.video_info.get_segment_duration()
        self.assertEqual(duration, 20.0)

    @patch('src.core.mediainfo.sp.run')
    def test_get_loudness(self, mock_run):
        mock_run.return_value = MagicMock(stderr="Summary:\nI: -23.0 LUFS\nLRA: 7.0 LU\nLRA high: -20.0 LUFS\nLRA low: -26.0 LUFS\nPeak: -1.0 dBTP")
        loudness = self.video_info.get_loudness()
        self.assertEqual(loudness['integrated_loudness'], -23.0)
        self.assertEqual(loudness['loudness_range'], 7.0)
        self.assertEqual(loudness['max_short-term_loudness'], -20.0)
        self.assertEqual(loudness['min-short-term_loudness'], -26.0)
        self.assertEqual(loudness['true_peak'], -1.0)

if __name__ == '__main__':
    unittest.main()
