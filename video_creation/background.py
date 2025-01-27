import json
import random
import re
import multiprocessing
import ffmpeg
from pathlib import Path
from random import randrange
from typing import Any, Tuple, Dict

import yt_dlp
from moviepy import VideoFileClip, AudioFileClip

from utils.settings import config


def load_background_options() -> Dict[str, Dict[str, Any]]:
    with open("./utils/background_videos.json") as json_file:
        video_options = json.load(json_file)

    with open("./utils/background_audios.json") as json_file:
        audio_options = json.load(json_file)

    video_options.pop("__comment", None)
    audio_options.pop("__comment", None)

    for name, details in video_options.items():
        if details[3] != "center":
            details[3] = lambda t: ("center", details[3] + t)

    return {"video": video_options, "audio": audio_options}


def get_and_download_background(mode: str) -> Tuple[str, Tuple[str, str, str, Any]]:
    choice = config["settings"]["background"].get(f"background_{mode}", "").casefold()
    if not choice or choice not in background_options[mode]:
        choice = random.choice(list(background_options[mode].keys()))
    background_config = background_options[mode][choice]

    Path(f"./assets/backgrounds/{mode}/").mkdir(parents=True, exist_ok=True)
    uri, filename, credit, *_ = background_config
    file_path = f"./assets/backgrounds/{mode}/{credit}-{filename}"

    if not Path(file_path).is_file():
        print(f"Downloading {filename} from {uri}")
        ydl_opts = {
            "format": "bestvideo[height<=1080][ext=mp4]" if mode == "video" else "bestaudio/best",
            "outtmpl": file_path,
            "retries": 10,
            "extract_audio": mode == "audio"
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([uri])

        print(f"Background {mode} downloaded successfully! 🎉")

    return file_path, background_config


def get_start_and_end_times(video_length: int, clip_length: int) -> Tuple[int, int]:
    video_length = int(video_length)
    clip_length = int(clip_length)
    
    initialValue = 180
    while clip_length <= video_length + initialValue:
        if initialValue == initialValue // 2:
            raise Exception("Your background is too short for this video length")
        initialValue //= 2

    random_time = randrange(initialValue, clip_length - video_length)
    return random_time, random_time + video_length


def chop_and_prepare_background(bg_config: Dict[str, Tuple[str, str, str, Any]], video_length: int, reddit_object: dict, width: int, height: int) -> Tuple[str, str, str]:
    reddit_id = re.sub(r"[^\w\s-]", "", reddit_object["id"])
    audio_path = f"assets/temp/{reddit_id}/background.mp3"
    video_path = f"assets/temp/{reddit_id}/background.mp4"
    output_path = f"assets/temp/{reddit_id}/background_noaudio.mp4"

    audio_file, audio_details = bg_config['audio']
    video_file, video_details = bg_config['video']

    if config["settings"]["background"]["background_audio_volume"] != 0:
        background_audio = AudioFileClip(audio_file)
        start_audio, end_audio = get_start_and_end_times(video_length, background_audio.duration)
        background_audio = background_audio.with_subclip(start_audio, end_audio)
        background_audio.write_audiofile(audio_path)

    background_video = VideoFileClip(video_file)
    start_video, end_video = get_start_and_end_times(video_length, background_video.duration)
    background_video = background_video.with_subclip(start_video, end_video)
    background_video.write_videofile(video_path)

    ffmpeg.input(video_path).filter("crop", f"ih*({width}/{height})", "ih").output(
        output_path,
        an=None,
        **{
            "c:v": "h264",
            "b:v": "20M",
            "b:a": "192k",
            "threads": multiprocessing.cpu_count(),
        },
    ).overwrite_output().run(quiet=True)

    return video_path, audio_path, output_path


background_options = load_background_options()