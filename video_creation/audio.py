import ffmpeg
from utils.settings import config


def merge_audio_tracks(story_audio: ffmpeg, background_audio_path: str):
    background_audio_volume = config["settings"]["background"]["background_audio_volume"]
    if background_audio_volume == 0:
        return story_audio
    background_audio = ffmpeg.input(background_audio_path).filter("volume", background_audio_volume)
    return ffmpeg.filter([story_audio, background_audio], "amix", duration="longest")